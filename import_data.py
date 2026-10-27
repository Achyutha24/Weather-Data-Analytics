#!/usr/bin/env python3
"""CSV and Kaggle Historical Weather Data Importer.

Ingests compatible weather CSV files (including Kaggle datasets) incrementally using
Pandas chunks. Validates rows, normalizes columns and datetimes, handles missing values,
and executes idempotent bulk upserts into local MongoDB.
"""

import sys
import os
import uuid
import argparse
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

import config
import db
import weather_utils

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("import_data")

# Flexible canonical column mapping dictionary (case-insensitive keys)
DEFAULT_COLUMN_MAPPINGS = {
    # Timestamps
    "date": "timestamp",
    "datetime": "timestamp",
    "time": "timestamp",
    "timestamp": "timestamp",
    "formatted_date": "timestamp",
    "dt": "timestamp",
    # City / Location
    "city": "city",
    "city_name": "city",
    "location": "city",
    "station": "city",
    # Temperature
    "temperature": "temperature_c",
    "temp": "temperature_c",
    "temperature_c": "temperature_c",
    "temperature_2m": "temperature_c",
    "temp_c": "temperature_c",
    "mean_temp": "temperature_c",
    "avg_temp": "temperature_c",
    # Relative Humidity
    "humidity": "relative_humidity_pct",
    "rel_humidity": "relative_humidity_pct",
    "relative_humidity": "relative_humidity_pct",
    "relative_humidity_pct": "relative_humidity_pct",
    "humidity_pct": "relative_humidity_pct",
    # Precipitation / Rainfall
    "precipitation": "precipitation_mm",
    "precip": "precipitation_mm",
    "precipitation_mm": "precipitation_mm",
    "rainfall": "precipitation_mm",
    "rain_mm": "precipitation_mm",
    "prcp": "precipitation_mm",
    # Wind Speed
    "wind_speed": "wind_speed_kmh",
    "windspeed": "wind_speed_kmh",
    "wind_speed_kmh": "wind_speed_kmh",
    "wind_speed_10m": "wind_speed_kmh",
    "wind_kph": "wind_speed_kmh",
    "wspd": "wind_speed_kmh",
    # Wind Direction
    "wind_direction": "wind_direction_deg",
    "wind_direction_deg": "wind_direction_deg",
    "wind_dir": "wind_direction_deg",
    "wdir": "wind_direction_deg",
    # Atmospheric Pressure
    "pressure": "pressure_msl_hpa",
    "pressure_msl_hpa": "pressure_msl_hpa",
    "surface_pressure": "pressure_msl_hpa",
    "sea_level_pressure": "pressure_msl_hpa",
    "pres": "pressure_msl_hpa",
    # Cloud Cover
    "cloud_cover": "cloud_cover_pct",
    "cloud_cover_pct": "cloud_cover_pct",
    "cloud": "cloud_cover_pct",
    "clouds": "cloud_cover_pct",
    # Weather Code
    "weather_code": "weather_code",
    "wmo_code": "weather_code",
    "weather_condition_code": "weather_code",
}


def resolve_row_fields(
    row_dict: Dict[str, Any],
    column_map: Dict[str, str],
    default_city: Optional[str] = None,
    default_granularity: str = "hourly",
    default_source: str = "csv_import",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Map a raw CSV row dictionary into standard observation format and validate.

    Returns:
        (canonical_doc, error_message)
    """
    mapped_raw: Dict[str, Any] = {
        "granularity": default_granularity,
        "source": default_source,
    }

    # Match raw column names against mapping dictionary
    for col, val in row_dict.items():
        if pd.isna(val) or val is None:
            continue
        col_norm = str(col).strip().lower().replace(" ", "_")
        target_field = column_map.get(col_norm)
        if target_field:
            mapped_raw[target_field] = val

    # Resolve city
    city_val = mapped_raw.get("city") or default_city
    if not city_val:
        return None, "Row missing city and no default city provided."

    # Look up city metadata from registry
    city_meta = config.get_city_metadata(str(city_val))
    if city_meta:
        mapped_raw["city"] = city_meta["city"]
        mapped_raw["country"] = city_meta["country"]
        mapped_raw["latitude"] = city_meta["latitude"]
        mapped_raw["longitude"] = city_meta["longitude"]
        mapped_raw["timezone"] = city_meta["timezone"]
    else:
        mapped_raw["city"] = str(city_val).strip()

    return weather_utils.validate_and_normalize_observation(
        mapped_raw,
        default_source=default_source,
        default_granularity=default_granularity,
    )


def import_csv_file(
    file_path: str,
    default_city: Optional[str] = None,
    granularity: str = "hourly",
    source_name: str = "csv_import",
    chunk_size: int = 5000,
    batch_size: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Import a historical weather CSV incrementally in chunks without memory exhaustion.

    Args:
        file_path: Path to the target CSV file.
        default_city: Default city name to use if city column is missing in CSV.
        granularity: Granularity of data ('hourly' or 'daily').
        source_name: Attribution label for the imported source.
        chunk_size: Number of CSV rows per pandas chunk.
        batch_size: MongoDB bulk write batch size.
        dry_run: If True, validate rows without inserting into MongoDB.

    Returns:
        Summary dict containing counts of read, accepted, rejected, inserted, updated records.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Specified CSV file does not exist: {file_path}")

    # Check MongoDB connectivity before reading
    if not dry_run:
        client = db.get_mongodb_client()
        db.ping_server(client)
        db.init_db_indexes(db.get_database(client))

    # Initialize run tracking
    run_id = f"import_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_record: Dict[str, Any] = {
        "run_id": run_id,
        "source": source_name,
        "file_path": os.path.abspath(file_path),
        "default_city": default_city,
        "granularity": granularity,
        "start_time": datetime.now(timezone.utc),
        "finish_time": None,
        "status": "in_progress",
        "records_read": 0,
        "records_accepted": 0,
        "records_rejected": 0,
        "records_inserted": 0,
        "records_updated": 0,
    }

    if not dry_run:
        try:
            db.log_ingestion_run(run_record)
        except Exception as exc:
            logger.warning("Could not log initial ingestion run: %s", exc)

    total_read = 0
    total_accepted = 0
    total_rejected = 0
    total_inserted = 0
    total_updated = 0
    total_matched = 0

    rejection_reasons: Dict[str, int] = {}

    logger.info("Starting chunked ingestion of CSV: %s (chunk_size=%d)", file_path, chunk_size)

    try:
        # Read file in chunks to handle big datasets smoothly
        for chunk_idx, df_chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size), 1):
            chunk_records = df_chunk.to_dict(orient="records")
            total_read += len(chunk_records)

            valid_docs: List[Dict[str, Any]] = []
            for row in chunk_records:
                doc, err = resolve_row_fields(
                    row,
                    column_map=DEFAULT_COLUMN_MAPPINGS,
                    default_city=default_city,
                    default_granularity=granularity,
                    default_source=source_name,
                )
                if doc:
                    valid_docs.append(doc)
                    total_accepted += 1
                else:
                    total_rejected += 1
                    err_key = err or "Validation failed"
                    rejection_reasons[err_key] = rejection_reasons.get(err_key, 0) + 1

            if not dry_run and valid_docs:
                write_res = db.bulk_upsert_observations(valid_docs, batch_size=batch_size)
                total_inserted += write_res["inserted"]
                total_updated += write_res["updated"]
                total_matched += write_res["matched"]

            logger.info("Processed Chunk %d: Read %d, Valid %d, Invalid %d",
                        chunk_idx, len(chunk_records), len(valid_docs), len(chunk_records) - len(valid_docs))

        status_str = "completed"
        err_msg = None
    except Exception as exc:
        logger.exception("CSV import aborted due to error: %s", exc)
        status_str = "failed"
        err_msg = str(exc)

    finish_time = datetime.now(timezone.utc)
    duration_s = (finish_time - run_record["start_time"]).total_seconds()

    summary = {
        "run_id": run_id,
        "status": status_str,
        "duration_seconds": duration_s,
        "total_read": total_read,
        "accepted": total_accepted,
        "rejected": total_rejected,
        "inserted": total_inserted,
        "updated": total_updated,
        "matched": total_matched,
        "rejection_reasons": rejection_reasons,
        "error_message": err_msg,
    }

    if not dry_run:
        try:
            db.update_ingestion_run(
                run_id,
                {
                    "finish_time": finish_time,
                    "status": status_str,
                    "records_read": total_read,
                    "records_accepted": total_accepted,
                    "records_rejected": total_rejected,
                    "records_inserted": total_inserted,
                    "records_updated": total_updated,
                    "duration_seconds": duration_s,
                    "error_message": err_msg,
                },
            )
        except Exception as exc:
            logger.warning("Could not update ingestion run status: %s", exc)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest historical weather CSV (including Kaggle files) incrementally into local MongoDB."
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        required=True,
        help="Path to CSV file to import.",
    )
    parser.add_argument(
        "--city",
        type=str,
        default=None,
        help="Default city name if city column is missing in CSV.",
    )
    parser.add_argument(
        "--granularity",
        choices=["hourly", "daily"],
        default="hourly",
        help="Observation frequency (default: hourly).",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="kaggle_csv",
        help="Source attribution identifier (default: kaggle_csv).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=5000,
        help="Pandas chunk size for incremental reading (default: 5000).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV rows without writing to MongoDB.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("   WEATHER DATA IMPORTER - CSV TO LOCAL MONGODB")
    print("=" * 70)
    print(f"File Path:    {args.file}")
    print(f"Default City: {args.city or 'Derived from CSV rows'}")
    print(f"Granularity:  {args.granularity}")
    print(f"Source:       {args.source}")
    print(f"Dry Run:      {args.dry_run}")
    print("=" * 70)

    try:
        summary = import_csv_file(
            file_path=args.file,
            default_city=args.city,
            granularity=args.granularity,
            source_name=args.source,
            chunk_size=args.chunk_size,
            dry_run=args.dry_run,
        )

        print("\n" + "=" * 70)
        print("   IMPORT SUMMARY")
        print("=" * 70)
        print(f"Status:            {summary['status'].upper()}")
        print(f"Duration:          {summary['duration_seconds']:.2f} seconds")
        print(f"Total Rows Read:   {summary['total_read']}")
        print(f"Rows Accepted:     {summary['accepted']}")
        print(f"Rows Rejected:     {summary['rejected']}")
        print(f"Rows Inserted:     {summary['inserted']}")
        print(f"Rows Updated:      {summary['updated']}")
        print(f"Rows Matched/Skip: {summary['matched']}")
        if summary["rejection_reasons"]:
            print("\nRejection Reasons Breakdown:")
            for reason, count in summary["rejection_reasons"].items():
                print(f"  - {reason}: {count} row(s)")
        print("=" * 70)
        return 0 if summary["status"] == "completed" else 1

    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        print("\n[FATAL ERROR] Cannot connect to local MongoDB Community Server!")
        print(f"Error details: {exc}")
        return 1
    except Exception as exc:
        print(f"\n[ERROR] Import failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
