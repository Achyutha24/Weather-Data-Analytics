"""Big-Data Analytics and MongoDB Aggregation Pipelines Module.

Executes all analytical queries directly inside MongoDB using high-performance aggregation
pipelines ($match, $group, $project, $sort, $limit, $dateTrunc, $facet) rather than pulling
entire datasets into Pandas in-memory.
"""

from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
from pymongo.collection import Collection

import config
import db
import weather_utils


def _build_match_filter(
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
    granularity: Optional[str] = "hourly",
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct a canonical $match query dictionary for aggregation stages."""
    match_filter: Dict[str, Any] = {}

    if cities:
        if isinstance(cities, str):
            match_filter["city"] = cities
        elif isinstance(cities, list) and len(cities) == 1:
            match_filter["city"] = cities[0]
        elif isinstance(cities, list) and len(cities) > 1:
            match_filter["city"] = {"$in": cities}

    if granularity:
        match_filter["granularity"] = granularity

    if source:
        match_filter["source"] = source

    # Parse and apply date range filters
    ts_filter: Dict[str, Any] = {}
    if start_date:
        start_dt = weather_utils.parse_timestamp(start_date)
        if start_dt:
            ts_filter["$gte"] = start_dt

    if end_date:
        end_dt = weather_utils.parse_timestamp(end_date)
        if end_dt:
            # If end_dt has time 00:00:00, include full day up to 23:59:59
            if end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0:
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            ts_filter["$lte"] = end_dt

    if ts_filter:
        match_filter["timestamp"] = ts_filter

    return match_filter


def get_database_summary(
    collection: Optional[Collection] = None,
) -> Dict[str, Any]:
    """Calculate high-level database metrics via MongoDB $facet aggregation pipeline.

    Returns:
        Dict with total_observations, city_count, cities_list, earliest_date, latest_date,
        avg_temp_c, min_temp_c, max_temp_c, total_precipitation_mm, sources.
    """
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    pipeline = [
        {
            "$facet": {
                "overall_stats": [
                    {
                        "$group": {
                            "_id": None,
                            "total_count": {"$sum": 1},
                            "earliest_ts": {"$min": "$timestamp"},
                            "latest_ts": {"$max": "$timestamp"},
                            "avg_temp": {"$avg": "$temperature_c"},
                            "min_temp": {"$min": "$temperature_c"},
                            "max_temp": {"$max": "$temperature_c"},
                            "total_precip": {"$sum": "$precipitation_mm"},
                        }
                    }
                ],
                "distinct_cities": [
                    {"$group": {"_id": "$city"}},
                    {"$sort": {"_id": 1}},
                ],
                "distinct_sources": [
                    {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                ],
                "granularities": [
                    {"$group": {"_id": "$granularity", "count": {"$sum": 1}}},
                ],
            }
        }
    ]

    try:
        results = list(col.aggregate(pipeline))
    except Exception as exc:
        return {"error": str(exc), "total_observations": 0}

    if not results or not results[0]:
        return {"total_observations": 0}

    facet = results[0]
    overall_list = facet.get("overall_stats", [])
    overall = overall_list[0] if overall_list else {}

    cities_list = [c["_id"] for c in facet.get("distinct_cities", []) if c.get("_id")]
    sources_list = [s["_id"] for s in facet.get("distinct_sources", []) if s.get("_id")]
    granularities_dict = {g["_id"]: g["count"] for g in facet.get("granularities", []) if g.get("_id")}

    return {
        "total_observations": overall.get("total_count", 0),
        "city_count": len(cities_list),
        "cities": cities_list,
        "earliest_date": overall.get("earliest_ts"),
        "latest_date": overall.get("latest_ts"),
        "avg_temperature_c": round(overall["avg_temp"], 2) if overall.get("avg_temp") is not None else None,
        "min_temperature_c": round(overall["min_temp"], 2) if overall.get("min_temp") is not None else None,
        "max_temperature_c": round(overall["max_temp"], 2) if overall.get("max_temp") is not None else None,
        "total_precipitation_mm": round(overall["total_precip"], 2) if overall.get("total_precip") is not None else 0.0,
        "sources": sources_list,
        "granularities": granularities_dict,
    }


def get_city_temperature_summary(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
    granularity: str = "hourly",
) -> pd.DataFrame:
    """Compute city-level temperature averages, minimums, and maximums using MongoDB pipeline."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities, start_date, end_date, granularity)
    match_filter["temperature_c"] = {"$ne": None}

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": "$city",
                "avg_temp_c": {"$avg": "$temperature_c"},
                "min_temp_c": {"$min": "$temperature_c"},
                "max_temp_c": {"$max": "$temperature_c"},
                "observations": {"$sum": 1},
            }
        },
        {
            "$project": {
                "city": "$_id",
                "_id": 0,
                "avg_temp_c": {"$round": ["$avg_temp_c", 2]},
                "min_temp_c": {"$round": ["$min_temp_c", 2]},
                "max_temp_c": {"$round": ["$max_temp_c", 2]},
                "temp_range_c": {"$round": [{"$subtract": ["$max_temp_c", "$min_temp_c"]}, 2]},
                "observations": 1,
            }
        },
        {"$sort": {"avg_temp_c": -1}},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "avg_temp_c", "min_temp_c", "max_temp_c", "temp_range_c", "observations"])


def get_daily_temperature_stats(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
) -> pd.DataFrame:
    """Aggregate daily temperature minimum, maximum, and average per city."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities, start_date, end_date, granularity="hourly")
    match_filter["temperature_c"] = {"$ne": None}

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": {
                    "city": "$city",
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                },
                "avg_temp": {"$avg": "$temperature_c"},
                "min_temp": {"$min": "$temperature_c"},
                "max_temp": {"$max": "$temperature_c"},
                "obs_count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "city": "$_id.city",
                "date": "$_id.date",
                "avg_temp_c": {"$round": ["$avg_temp", 2]},
                "min_temp_c": {"$round": ["$min_temp", 2]},
                "max_temp_c": {"$round": ["$max_temp", 2]},
                "obs_count": 1,
            }
        },
        {"$sort": {"date": 1, "city": 1}},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "date", "avg_temp_c", "min_temp_c", "max_temp_c", "obs_count"])


def get_monthly_temperature_trends(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
) -> pd.DataFrame:
    """Aggregate monthly temperature trends per city."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities, start_date, end_date)
    match_filter["temperature_c"] = {"$ne": None}

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": {
                    "city": "$city",
                    "year_month": {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}},
                },
                "avg_temp": {"$avg": "$temperature_c"},
                "min_temp": {"$min": "$temperature_c"},
                "max_temp": {"$max": "$temperature_c"},
                "obs_count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "city": "$_id.city",
                "year_month": "$_id.year_month",
                "avg_temp_c": {"$round": ["$avg_temp", 2]},
                "min_temp_c": {"$round": ["$min_temp", 2]},
                "max_temp_c": {"$round": ["$max_temp", 2]},
                "obs_count": 1,
            }
        },
        {"$sort": {"year_month": 1, "city": 1}},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "year_month", "avg_temp_c", "min_temp_c", "max_temp_c", "obs_count"])


def get_annual_comparison(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
) -> pd.DataFrame:
    """Compare weather metrics across years per city."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities)

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": {
                    "city": "$city",
                    "year": {"$year": "$timestamp"},
                },
                "avg_temp": {"$avg": "$temperature_c"},
                "min_temp": {"$min": "$temperature_c"},
                "max_temp": {"$max": "$temperature_c"},
                "total_precip": {"$sum": "$precipitation_mm"},
                "avg_humidity": {"$avg": "$relative_humidity_pct"},
                "avg_wind": {"$avg": "$wind_speed_kmh"},
                "observations": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "city": "$_id.city",
                "year": "$_id.year",
                "avg_temp_c": {"$round": ["$avg_temp", 2]},
                "min_temp_c": {"$round": ["$min_temp", 2]},
                "max_temp_c": {"$round": ["$max_temp", 2]},
                "total_precip_mm": {"$round": ["$total_precip", 2]},
                "avg_humidity_pct": {"$round": ["$avg_humidity", 2]},
                "avg_wind_kmh": {"$round": ["$avg_wind", 2]},
                "observations": 1,
            }
        },
        {"$sort": {"year": 1, "city": 1}},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "year", "avg_temp_c", "min_temp_c", "max_temp_c", "total_precip_mm", "avg_humidity_pct", "avg_wind_kmh", "observations"])


def get_city_precipitation_totals(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
) -> pd.DataFrame:
    """Calculate cumulative rainfall and precipitation statistics per city."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities, start_date, end_date)
    match_filter["precipitation_mm"] = {"$ne": None}

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": "$city",
                "total_rainfall_mm": {"$sum": "$precipitation_mm"},
                "max_single_event_mm": {"$max": "$precipitation_mm"},
                "avg_event_mm": {"$avg": "$precipitation_mm"},
                "rain_hours_count": {
                    "$sum": {"$cond": [{"$gt": ["$precipitation_mm", 0.0]}, 1, 0]}
                },
                "total_observations": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "city": "$_id",
                "total_rainfall_mm": {"$round": ["$total_rainfall_mm", 2]},
                "max_single_event_mm": {"$round": ["$max_single_event_mm", 2]},
                "avg_event_mm": {"$round": ["$avg_event_mm", 2]},
                "rain_hours_count": 1,
                "dry_hours_count": {"$subtract": ["$total_observations", "$rain_hours_count"]},
                "rainy_fraction_pct": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$rain_hours_count", "$total_observations"]}, 100]},
                        2,
                    ]
                },
            }
        },
        {"$sort": {"total_rainfall_mm": -1}},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "total_rainfall_mm", "max_single_event_mm", "avg_event_mm", "rain_hours_count", "dry_hours_count", "rainy_fraction_pct"])


def get_monthly_rainfall_trends(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
) -> pd.DataFrame:
    """Compute monthly rainfall totals per city."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities, start_date, end_date)
    match_filter["precipitation_mm"] = {"$ne": None}

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": {
                    "city": "$city",
                    "year_month": {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}},
                },
                "total_rainfall_mm": {"$sum": "$precipitation_mm"},
                "max_hour_mm": {"$max": "$precipitation_mm"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "city": "$_id.city",
                "year_month": "$_id.year_month",
                "total_rainfall_mm": {"$round": ["$total_rainfall_mm", 2]},
                "max_hour_mm": {"$round": ["$max_hour_mm", 2]},
            }
        },
        {"$sort": {"year_month": 1, "city": 1}},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "year_month", "total_rainfall_mm", "max_hour_mm"])


def get_wettest_dates(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
    limit: int = 20,
) -> pd.DataFrame:
    """Find the wettest dates aggregated by daily total precipitation."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities, start_date, end_date)
    match_filter["precipitation_mm"] = {"$gt": 0.0}

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": {
                    "city": "$city",
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                },
                "total_daily_rainfall_mm": {"$sum": "$precipitation_mm"},
                "peak_hourly_rainfall_mm": {"$max": "$precipitation_mm"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "city": "$_id.city",
                "date": "$_id.date",
                "total_daily_rainfall_mm": {"$round": ["$total_daily_rainfall_mm", 2]},
                "peak_hourly_rainfall_mm": {"$round": ["$peak_hourly_rainfall_mm", 2]},
            }
        },
        {"$sort": {"total_daily_rainfall_mm": -1}},
        {"$limit": limit},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "date", "total_daily_rainfall_mm", "peak_hourly_rainfall_mm"])


def get_high_wind_observations(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    threshold_kmh: float = 30.0,
    limit: int = 50,
) -> pd.DataFrame:
    """Retrieve observations exceeding a user-configurable wind speed threshold."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities)
    match_filter["wind_speed_kmh"] = {"$gte": float(threshold_kmh)}

    pipeline = [
        {"$match": match_filter},
        {
            "$project": {
                "_id": 0,
                "city": 1,
                "timestamp": 1,
                "wind_speed_kmh": 1,
                "wind_direction_deg": 1,
                "temperature_c": 1,
                "relative_humidity_pct": 1,
                "weather_code": 1,
            }
        },
        {"$sort": {"wind_speed_kmh": -1}},
        {"$limit": limit},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "timestamp", "wind_speed_kmh", "wind_direction_deg", "temperature_c", "relative_humidity_pct", "weather_code"])


def get_humidity_summary(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
) -> pd.DataFrame:
    """Compute relative humidity statistics per city."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities, start_date, end_date)
    match_filter["relative_humidity_pct"] = {"$ne": None}

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": "$city",
                "avg_humidity_pct": {"$avg": "$relative_humidity_pct"},
                "min_humidity_pct": {"$min": "$relative_humidity_pct"},
                "max_humidity_pct": {"$max": "$relative_humidity_pct"},
                "observations": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "city": "$_id",
                "avg_humidity_pct": {"$round": ["$avg_humidity_pct", 2]},
                "min_humidity_pct": {"$round": ["$min_humidity_pct", 2]},
                "max_humidity_pct": {"$round": ["$max_humidity_pct", 2]},
                "observations": 1,
            }
        },
        {"$sort": {"avg_humidity_pct": -1}},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["city", "avg_humidity_pct", "min_humidity_pct", "max_humidity_pct", "observations"])


def get_weather_code_distribution(
    collection: Optional[Collection] = None,
    city: Optional[str] = None,
) -> pd.DataFrame:
    """Compute frequency of WMO weather codes with descriptive interpretation labels."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter: Dict[str, Any] = {"weather_code": {"$ne": None}}
    if city:
        match_filter["city"] = city

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": "$weather_code",
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "weather_code": "$_id",
                "count": 1,
            }
        },
        {"$sort": {"count": -1}},
    ]

    docs = list(col.aggregate(pipeline))
    df = pd.DataFrame(docs) if docs else pd.DataFrame(columns=["weather_code", "count"])
    if not df.empty:
        df["description"] = df["weather_code"].apply(config.get_wmo_description)
    else:
        df["description"] = pd.Series(dtype=str)
    return df


def get_extreme_temperatures(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    top_n: int = 10,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Retrieve top N highest and top N lowest temperature records ever recorded."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities)
    match_filter["temperature_c"] = {"$ne": None}

    # Highest
    high_pipeline = [
        {"$match": match_filter},
        {"$sort": {"temperature_c": -1}},
        {"$limit": top_n},
        {
            "$project": {
                "_id": 0,
                "city": 1,
                "timestamp": 1,
                "temperature_c": 1,
                "relative_humidity_pct": 1,
                "wind_speed_kmh": 1,
                "weather_code": 1,
            }
        },
    ]

    # Lowest
    low_pipeline = [
        {"$match": match_filter},
        {"$sort": {"temperature_c": 1}},
        {"$limit": top_n},
        {
            "$project": {
                "_id": 0,
                "city": 1,
                "timestamp": 1,
                "temperature_c": 1,
                "relative_humidity_pct": 1,
                "wind_speed_kmh": 1,
                "weather_code": 1,
            }
        },
    ]

    high_docs = list(col.aggregate(high_pipeline))
    low_docs = list(col.aggregate(low_pipeline))

    df_high = pd.DataFrame(high_docs) if high_docs else pd.DataFrame(columns=["city", "timestamp", "temperature_c", "relative_humidity_pct", "wind_speed_kmh", "weather_code"])
    df_low = pd.DataFrame(low_docs) if low_docs else pd.DataFrame(columns=["city", "timestamp", "temperature_c", "relative_humidity_pct", "wind_speed_kmh", "weather_code"])

    return df_high, df_low


def get_observation_counts_by_period(
    collection: Optional[Collection] = None,
    group_by: str = "year_month",
) -> pd.DataFrame:
    """Aggregate observation counts grouped by date period (year, year_month, or city)."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    format_str = "%Y-%m"
    if group_by == "year":
        format_str = "%Y"
    elif group_by == "date":
        format_str = "%Y-%m-%d"

    pipeline = [
        {
            "$group": {
                "_id": {
                    "period": {"$dateToString": {"format": format_str, "date": "$timestamp"}},
                    "city": "$city",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "period": "$_id.period",
                "city": "$_id.city",
                "observations": "$count",
            }
        },
        {"$sort": {"period": 1, "city": 1}},
    ]

    docs = list(col.aggregate(pipeline))
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=["period", "city", "observations"])


def get_data_quality_report(
    collection: Optional[Collection] = None,
) -> Dict[str, Any]:
    """Calculate completeness and null/missing value metrics for all meteorological fields."""
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_records": {"$sum": 1},
                "missing_temp": {"$sum": {"$cond": [{"$eq": ["$temperature_c", None]}, 1, 0]}},
                "missing_humidity": {"$sum": {"$cond": [{"$eq": ["$relative_humidity_pct", None]}, 1, 0]}},
                "missing_precip": {"$sum": {"$cond": [{"$eq": ["$precipitation_mm", None]}, 1, 0]}},
                "missing_wind_speed": {"$sum": {"$cond": [{"$eq": ["$wind_speed_kmh", None]}, 1, 0]}},
                "missing_wind_dir": {"$sum": {"$cond": [{"$eq": ["$wind_direction_deg", None]}, 1, 0]}},
                "missing_pressure": {"$sum": {"$cond": [{"$eq": ["$pressure_msl_hpa", None]}, 1, 0]}},
                "missing_cloud_cover": {"$sum": {"$cond": [{"$eq": ["$cloud_cover_pct", None]}, 1, 0]}},
                "missing_weather_code": {"$sum": {"$cond": [{"$eq": ["$weather_code", None]}, 1, 0]}},
            }
        }
    ]

    docs = list(col.aggregate(pipeline))
    if not docs:
        return {"total_records": 0, "metrics": {}}

    data = docs[0]
    total = data.get("total_records", 0)
    if total == 0:
        return {"total_records": 0, "metrics": {}}

    metrics = {}
    fields = [
        ("temperature_c", "missing_temp"),
        ("relative_humidity_pct", "missing_humidity"),
        ("precipitation_mm", "missing_precip"),
        ("wind_speed_kmh", "missing_wind_speed"),
        ("wind_direction_deg", "missing_wind_dir"),
        ("pressure_msl_hpa", "missing_pressure"),
        ("cloud_cover_pct", "missing_cloud_cover"),
        ("weather_code", "missing_weather_code"),
    ]

    for field_name, missing_key in fields:
        missing_count = data.get(missing_key, 0)
        valid_count = total - missing_count
        completeness = round((valid_count / total) * 100, 2)
        metrics[field_name] = {
            "valid_count": valid_count,
            "missing_count": missing_count,
            "completeness_pct": completeness,
        }

    return {"total_records": total, "metrics": metrics}


def get_relationship_sample(
    collection: Optional[Collection] = None,
    cities: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
    sample_size: int = 3000,
) -> pd.DataFrame:
    """Retrieve a bounded, representative sample of observations for scatter plots and correlations.

    Uses MongoDB $match followed by $sample (or bounded limit) to prevent browser/memory overload.
    Note: Statistical correlations show mathematical association, NOT causation.
    """
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(cities, start_date, end_date)
    # Require at least temperature and humidity
    match_filter["temperature_c"] = {"$ne": None}
    match_filter["relative_humidity_pct"] = {"$ne": None}

    pipeline = [
        {"$match": match_filter},
        {"$sample": {"size": sample_size}},
        {
            "$project": {
                "_id": 0,
                "city": 1,
                "timestamp": 1,
                "temperature_c": 1,
                "relative_humidity_pct": 1,
                "precipitation_mm": 1,
                "wind_speed_kmh": 1,
                "pressure_msl_hpa": 1,
                "cloud_cover_pct": 1,
            }
        },
    ]

    try:
        docs = list(col.aggregate(pipeline))
    except Exception:
        # Fallback if $sample fails on small datasets
        pipeline_fallback = [
            {"$match": match_filter},
            {"$limit": sample_size},
            {
                "$project": {
                    "_id": 0,
                    "city": 1,
                    "timestamp": 1,
                    "temperature_c": 1,
                    "relative_humidity_pct": 1,
                    "precipitation_mm": 1,
                    "wind_speed_kmh": 1,
                    "pressure_msl_hpa": 1,
                    "cloud_cover_pct": 1,
                }
            },
        ]
        docs = list(col.aggregate(pipeline_fallback))

    cols = ["city", "timestamp", "temperature_c", "relative_humidity_pct", "precipitation_mm", "wind_speed_kmh", "pressure_msl_hpa", "cloud_cover_pct"]
    return pd.DataFrame(docs) if docs else pd.DataFrame(columns=cols)


def get_explorer_records(
    collection: Optional[Collection] = None,
    city: Optional[str] = None,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
    source: Optional[str] = None,
    granularity: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort_field: str = "timestamp",
    sort_order: int = -1,
) -> Tuple[pd.DataFrame, int]:
    """Retrieve paginated, filtered weather records from MongoDB without loading the entire collection.

    Returns:
        (DataFrame of page rows, total matching count)
    """
    col = collection if collection is not None else db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)

    match_filter = _build_match_filter(
        cities=[city] if city and city != "All Cities" else None,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity if granularity and granularity != "All" else None,
        source=source if source and source != "All" else None,
    )

    total_matching = col.count_documents(match_filter)
    if total_matching == 0:
        return pd.DataFrame(), 0

    skip_count = max(0, (page - 1) * page_size)

    cursor = (
        col.find(match_filter, {"_id": 0})
        .sort(sort_field, sort_order)
        .skip(skip_count)
        .limit(page_size)
    )

    docs = list(cursor)
    return pd.DataFrame(docs), total_matching
