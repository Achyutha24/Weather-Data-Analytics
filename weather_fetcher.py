#!/usr/bin/env python3
"""Weather Data Ingestion Module from Open-Meteo Historical Archive API.

Fetches historical hourly weather observations for configured Indian cities,
validates and cleans observations, and performs idempotent bulk upserts into local MongoDB.
Tracks ingestion history in the ingestion_runs collection.
"""

import sys
import uuid
import time
import argparse
import logging
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional
import requests
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

import config
import db
import weather_utils

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("weather_fetcher")

SOURCE_ATTRIBUTION = (
    "Historical weather data retrieved from Open-Meteo Historical Weather API "
    "(https://open-meteo.com/). Note: Historical reanalysis observations are derived from "
    "high-resolution numerical weather models (ECMWF ERA5 / ERA5-Land) combined with station inputs."
)


def fetch_open_meteo_chunk(
    latitude: float,
    longitude: float,
    timezone_str: str,
    start_d: date,
    end_d: date,
    max_retries: int = 3,
    timeout: int = 25,
) -> Optional[Dict[str, Any]]:
    """Fetch hourly weather data from Open-Meteo Archive API for a single date slice with exponential backoff.

    Args:
        latitude: Station latitude.
        longitude: Station longitude.
        timezone_str: IANA timezone identifier (e.g., 'Asia/Kolkata').
        start_d: Chunk start date.
        end_d: Chunk end date.
        max_retries: Number of retry attempts.
        timeout: HTTP request timeout in seconds.

    Returns:
        JSON dictionary from API response or None if failed.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_d.strftime("%Y-%m-%d"),
        "end_date": end_d.strftime("%Y-%m-%d"),
        "hourly": ",".join(config.API_HOURLY_VARIABLES),
        "timezone": timezone_str,
    }

    url = config.OPEN_METEO_ARCHIVE_URL

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Requesting %s to %s (attempt %d/%d)...", start_d, end_d, attempt, max_retries)
            resp = requests.get(url, params=params, timeout=timeout)

            if resp.status_code == 200:
                data = resp.json()
                if "hourly" in data and "time" in data["hourly"]:
                    return data
                logger.warning("API returned 200 but payload missing 'hourly.time'. Response: %s", resp.text[:200])
                return None

            if resp.status_code == 429:
                wait_time = 2 ** attempt * 2
                logger.warning("Rate limit encountered (HTTP 429). Backing off for %d seconds...", wait_time)
                time.sleep(wait_time)
                continue

            logger.warning("HTTP %d error from Open-Meteo: %s", resp.status_code, resp.text[:200])
            time.sleep(2 ** attempt)

        except (requests.RequestException, TimeoutError) as exc:
            logger.warning("Network error on attempt %d: %s", attempt, exc)
            time.sleep(2 ** attempt)

    logger.error("Failed to fetch chunk %s to %s after %d retries.", start_d, end_d, max_retries)
    return None


def parse_open_meteo_payload(
    city_meta: Dict[str, Any],
    api_payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Parse raw Open-Meteo API payload into canonical weather observation dictionaries."""
    hourly_block = api_payload.get("hourly", {})
    timestamps = hourly_block.get("time", [])
    if not timestamps:
        return []

    num_records = len(timestamps)
    city_name = city_meta["city"]
    country = city_meta["country"]
    lat = city_meta["latitude"]
    lon = city_meta["longitude"]
    tz = city_meta["timezone"]

    extracted_docs: List[Dict[str, Any]] = []

    for i in range(num_records):
        raw_doc: Dict[str, Any] = {
            "city": city_name,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
            "timestamp": timestamps[i],
            "granularity": "hourly",
            "source": "open_meteo",
        }

        # Extract meteorological metrics
        for api_var, doc_field in config.API_FIELD_MAPPING.items():
            series = hourly_block.get(api_var)
            if series and i < len(series):
                raw_doc[doc_field] = series[i]
            else:
                raw_doc[doc_field] = None

        canonical_doc, err = weather_utils.validate_and_normalize_observation(
            raw_doc,
            default_source="open_meteo",
            default_granularity="hourly",
        )
        if canonical_doc:
            extracted_docs.append(canonical_doc)
        else:
            logger.debug("Skipping invalid record for %s at index %d: %s", city_name, i, err)

    return extracted_docs


def ingest_city_weather(
    city_name: str,
    start_d: date,
    end_d: date,
    dry_run: bool = False,
) -> Dict[str, int]:
    """Ingest weather data for a single city over the specified date range.

    Returns:
        Dict with total_fetched, accepted, inserted, updated, and skipped counts.
    """
    city_meta = config.get_city_metadata(city_name)
    if not city_meta:
        logger.error("City '%s' not found in registry. Skipping.", city_name)
        return {"fetched": 0, "accepted": 0, "inserted": 0, "updated": 0, "rejected": 0}

    logger.info("Processing city: %s (Lat: %s, Lon: %s, TZ: %s)",
                city_name, city_meta["latitude"], city_meta["longitude"], city_meta["timezone"])

    # Chunk date range into 365-day slices
    chunks = weather_utils.chunk_date_range(start_d, end_d, max_days=365)
    logger.info("Date range %s to %s split into %d chunk(s)", start_d, end_d, len(chunks))

    total_fetched = 0
    total_accepted = 0
    total_inserted = 0
    total_updated = 0
    total_matched = 0

    for idx, (c_start, c_end) in enumerate(chunks, 1):
        logger.info("[%s] Fetching chunk %d/%d (%s to %s)...", city_name, idx, len(chunks), c_start, c_end)
        payload = fetch_open_meteo_chunk(
            latitude=city_meta["latitude"],
            longitude=city_meta["longitude"],
            timezone_str=city_meta["timezone"],
            start_d=c_start,
            end_d=c_end,
        )

        if not payload:
            logger.warning("[%s] No data returned for chunk %s to %s", city_name, c_start, c_end)
            continue

        raw_records = len(payload.get("hourly", {}).get("time", []))
        total_fetched += raw_records

        canonical_docs = parse_open_meteo_payload(city_meta, payload)
        total_accepted += len(canonical_docs)

        if not dry_run and canonical_docs:
            write_res = db.bulk_upsert_observations(canonical_docs)
            total_inserted += write_res["inserted"]
            total_updated += write_res["updated"]
            total_matched += write_res["matched"]
            logger.info("[%s Chunk %d/%d] Upserted: %d new, %d updated, %d matched",
                        city_name, idx, len(chunks), write_res["inserted"], write_res["updated"], write_res["matched"])
        elif dry_run:
            logger.info("[%s Chunk %d/%d Dry Run] Validated %d canonical records",
                        city_name, idx, len(chunks), len(canonical_docs))

        # Polite delay to respect API rate limits
        time.sleep(0.5)

    return {
        "fetched": total_fetched,
        "accepted": total_accepted,
        "rejected": total_fetched - total_accepted,
        "inserted": total_inserted,
        "updated": total_updated,
        "matched": total_matched,
    }


def run_fetcher(
    cities: Optional[List[str]] = None,
    start_date_str: str = "2021-01-01",
    end_date_str: str = "2025-12-31",
    dry_run: bool = False,
) -> int:
    """Main orchestration pipeline for historical weather data fetching."""
    print("=" * 70)
    print("   WEATHER FETCHER - OPEN-METEO TO LOCAL MONGODB")
    print("=" * 70)
    print(f"Source:           {config.OPEN_METEO_ARCHIVE_URL}")
    print(f"Attribution:      {SOURCE_ATTRIBUTION}")
    print(f"Target Database:  {config.MONGODB_DATABASE} at {config.MONGODB_URI}")
    print(f"Date Range:       {start_date_str} to {end_date_str}")
    print("=" * 70)

    # 1. Check local MongoDB connection FIRST before making API requests
    if not dry_run:
        try:
            client = db.get_mongodb_client()
            info = db.ping_server(client)
            print(f"[OK] Connected to local MongoDB Community Server (v{info.get('version')})")
            db.init_db_indexes(db.get_database(client))
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            print("\n[FATAL ERROR] Cannot connect to local MongoDB Community Server!")
            print("Please ensure MongoDB Community Server is installed and running:")
            print("   PowerShell: Get-Service MongoDB")
            print("   PowerShell: Start-Service MongoDB")
            print(f"Error details: {exc}")
            return 1

    # 2. Validate date range
    try:
        start_d, end_d = weather_utils.validate_date_range(start_date_str, end_date_str)
    except ValueError as val_err:
        print(f"[ERROR] Date validation error: {val_err}")
        return 1

    # 3. Resolve target cities
    all_known_cities = list(config.CITY_REGISTRY.keys())
    if not cities or "all" in [c.lower() for c in cities]:
        target_cities = all_known_cities
    else:
        target_cities = []
        for c in cities:
            meta = config.get_city_metadata(c)
            if meta:
                target_cities.append(meta["city"])
            else:
                print(f"[WARNING] City '{c}' is not recognized in registry. Available: {', '.join(all_known_cities)}")

    if not target_cities:
        print("[ERROR] No valid target cities selected. Aborting.")
        return 1

    print(f"Selected Cities ({len(target_cities)}): {', '.join(target_cities)}")

    # 4. Ingestion run logging
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_record: Dict[str, Any] = {
        "run_id": run_id,
        "source": "open_meteo",
        "requested_cities": target_cities,
        "requested_date_range": {"start": start_date_str, "end": end_date_str},
        "start_time": datetime.now(timezone.utc),
        "finish_time": None,
        "status": "in_progress",
        "records_read": 0,
        "records_accepted": 0,
        "records_rejected": 0,
        "records_inserted": 0,
        "records_updated": 0,
        "error_message": None,
    }

    if not dry_run:
        try:
            db.log_ingestion_run(run_record)
        except Exception as exc:
            logger.warning("Could not log initial ingestion run: %s", exc)

    # 5. Execute ingestion loop
    grand_totals = {"fetched": 0, "accepted": 0, "rejected": 0, "inserted": 0, "updated": 0, "matched": 0}

    try:
        for city in target_cities:
            city_stats = ingest_city_weather(city, start_d, end_d, dry_run=dry_run)
            for k in grand_totals:
                grand_totals[k] += city_stats.get(k, 0)

        status_str = "completed"
        err_msg = None
    except Exception as exc:
        logger.exception("Ingestion run aborted due to exception: %s", exc)
        status_str = "failed"
        err_msg = str(exc)

    finish_time = datetime.now(timezone.utc)
    duration_s = (finish_time - run_record["start_time"]).total_seconds()

    # 6. Update run record
    if not dry_run:
        try:
            db.update_ingestion_run(
                run_id,
                {
                    "finish_time": finish_time,
                    "status": status_str,
                    "records_read": grand_totals["fetched"],
                    "records_accepted": grand_totals["accepted"],
                    "records_rejected": grand_totals["rejected"],
                    "records_inserted": grand_totals["inserted"],
                    "records_updated": grand_totals["updated"],
                    "error_message": err_msg,
                    "duration_seconds": duration_s,
                },
            )
        except Exception as exc:
            logger.warning("Could not update ingestion run record: %s", exc)

    # 7. Print summary
    print("\n" + "=" * 70)
    print("   INGESTION SUMMARY")
    print("=" * 70)
    print(f"Status:            {status_str.upper()}")
    print(f"Duration:          {duration_s:.1f} seconds")
    print(f"Total API Records: {grand_totals['fetched']}")
    print(f"Accepted & Valid:  {grand_totals['accepted']}")
    print(f"Rejected/Invalid:  {grand_totals['rejected']}")
    print(f"Inserted (New):    {grand_totals['inserted']}")
    print(f"Updated (Set):     {grand_totals['updated']}")
    print(f"Matched Unchanged: {grand_totals['matched']}")
    print("=" * 70)

    return 0 if status_str == "completed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch historical weather observations from Open-Meteo into local MongoDB."
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        help="List of city names to fetch (e.g. --cities Bengaluru Delhi Mumbai) or 'all'.",
        default=["all"],
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2021-01-01",
        help="Start date in YYYY-MM-DD format (default: 2021-01-01).",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2025-12-31",
        help="End date in YYYY-MM-DD format (default: 2025-12-31).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate without writing records to MongoDB.",
    )

    args = parser.parse_args()
    return run_fetcher(
        cities=args.cities,
        start_date_str=args.start_date,
        end_date_str=args.end_date,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
