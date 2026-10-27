"""Unit tests for analytics module and MongoDB aggregation pipelines.

Tests pipeline construction, empty query results, null handling,
and aggregation outputs using mongomock.
"""

from datetime import datetime, timezone, date
import pytest
import mongomock
import pandas as pd

import analytics
import config


@pytest.fixture
def mock_collection():
    """Create an in-memory mongomock collection populated with test weather records."""
    client = mongomock.MongoClient()
    col = client["test_weather"]["weather_observations"]

    test_docs = [
        {
            "city": "Bengaluru",
            "country": "India",
            "timestamp": datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            "granularity": "hourly",
            "temperature_c": 26.5,
            "relative_humidity_pct": 60.0,
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 12.0,
            "pressure_msl_hpa": 1012.0,
            "weather_code": 1,
            "source": "open_meteo",
        },
        {
            "city": "Bengaluru",
            "country": "India",
            "timestamp": datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc),
            "granularity": "hourly",
            "temperature_c": 28.5,
            "relative_humidity_pct": 55.0,
            "precipitation_mm": 5.2,
            "wind_speed_kmh": 14.5,
            "pressure_msl_hpa": 1011.5,
            "weather_code": 61,
            "source": "open_meteo",
        },
        {
            "city": "Delhi",
            "country": "India",
            "timestamp": datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            "granularity": "hourly",
            "temperature_c": 15.0,
            "relative_humidity_pct": 80.0,
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 8.0,
            "pressure_msl_hpa": 1016.0,
            "weather_code": 45,
            "source": "open_meteo",
        },
        {
            "city": "Delhi",
            "country": "India",
            "timestamp": datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc),
            "granularity": "hourly",
            "temperature_c": None,  # Missing observation
            "relative_humidity_pct": 82.0,
            "precipitation_mm": None,
            "wind_speed_kmh": 35.0,  # High wind
            "pressure_msl_hpa": 1015.5,
            "weather_code": 45,
            "source": "open_meteo",
        },
    ]
    col.insert_many(test_docs)
    return col


def test_build_match_filter():
    """Verify $match filter construction with dates, cities, and granularities."""
    # Single city
    f1 = analytics._build_match_filter(cities="Bengaluru")
    assert f1["city"] == "Bengaluru"
    assert f1["granularity"] == "hourly"

    # Multiple cities
    f2 = analytics._build_match_filter(cities=["Bengaluru", "Delhi"])
    assert "$in" in f2["city"]
    assert "Delhi" in f2["city"]["$in"]

    # Date range
    f3 = analytics._build_match_filter(start_date="2023-01-01", end_date="2023-01-31")
    assert "$gte" in f3["timestamp"]
    assert "$lte" in f3["timestamp"]


def test_get_database_summary_with_mock(mock_collection):
    """Verify summary metrics calculation using mock collection."""
    summary = analytics.get_database_summary(collection=mock_collection)
    assert summary["total_observations"] == 4
    assert summary["city_count"] == 2
    assert "Bengaluru" in summary["cities"]
    assert "Delhi" in summary["cities"]
    assert summary["total_precipitation_mm"] == 5.2


def test_empty_database_handling():
    """Verify all analytics functions handle empty collections without exceptions."""
    client = mongomock.MongoClient()
    empty_col = client["empty_db"]["weather_observations"]

    # Summary
    summary = analytics.get_database_summary(collection=empty_col)
    assert summary["total_observations"] == 0

    # City temperatures
    df_temp = analytics.get_city_temperature_summary(collection=empty_col)
    assert isinstance(df_temp, pd.DataFrame)
    assert df_temp.empty
    assert "city" in df_temp.columns

    # Daily stats
    df_daily = analytics.get_daily_temperature_stats(collection=empty_col)
    assert df_daily.empty

    # Rainfall totals
    df_rain = analytics.get_city_precipitation_totals(collection=empty_col)
    assert df_rain.empty

    # Extreme temperatures
    high_df, low_df = analytics.get_extreme_temperatures(collection=empty_col)
    assert high_df.empty
    assert low_df.empty

    # Data quality
    dq = analytics.get_data_quality_report(collection=empty_col)
    assert dq["total_records"] == 0


def test_data_quality_null_detection(mock_collection):
    """Verify null/missing counts detection in data quality reporting."""
    dq = analytics.get_data_quality_report(collection=mock_collection)
    assert dq["total_records"] == 4
    metrics = dq["metrics"]
    # Delhi has 1 record with temperature_c = None
    assert metrics["temperature_c"]["missing_count"] == 1
    assert metrics["temperature_c"]["valid_count"] == 3
    assert metrics["temperature_c"]["completeness_pct"] == 75.0
