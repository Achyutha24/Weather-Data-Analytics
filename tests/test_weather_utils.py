"""Unit tests for weather_utils module.

Tests timestamp parsing, numeric sanitization, meteorological bounds,
schema validation, date-range chunking, and idempotent document filters.
"""

from datetime import datetime, timezone, date
import pytest
import weather_utils


def test_parse_timestamp_formats():
    """Verify parsing across ISO strings, space-delimited, and invalid timestamps."""
    # Standard ISO
    ts1 = weather_utils.parse_timestamp("2023-05-15T14:30:00")
    assert ts1 is not None
    assert ts1.year == 2023 and ts1.month == 5 and ts1.day == 15
    assert ts1.hour == 14 and ts1.minute == 30
    assert ts1.tzinfo == timezone.utc

    # Space separated
    ts2 = weather_utils.parse_timestamp("2023-05-15 14:30:00")
    assert ts2 is not None
    assert ts2 == ts1

    # Date only
    ts3 = weather_utils.parse_timestamp("2023-05-15")
    assert ts3 is not None
    assert ts3.day == 15 and ts3.hour == 0

    # Datetime object
    dt_input = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert weather_utils.parse_timestamp(dt_input) == dt_input

    # Null, empty, and invalid strings
    assert weather_utils.parse_timestamp(None) is None
    assert weather_utils.parse_timestamp("") is None
    assert weather_utils.parse_timestamp("invalid-date-string") is None
    assert weather_utils.parse_timestamp("NaN") is None


def test_sanitize_float_and_missing_values():
    """Verify numeric sanitization handles bounds and does NOT silently invent zeros."""
    assert weather_utils.sanitize_float(25.4) == 25.4
    assert weather_utils.sanitize_float(" 32.55 ") == 32.55
    assert weather_utils.sanitize_float("-10.2") == -10.2

    # Strings representing null/missing should remain None
    assert weather_utils.sanitize_float("nan") is None
    assert weather_utils.sanitize_float("null") is None
    assert weather_utils.sanitize_float("NA") is None
    assert weather_utils.sanitize_float("-") is None
    assert weather_utils.sanitize_float(None) is None

    # Bounds check
    assert weather_utils.sanitize_float(150.0, min_val=-90.0, max_val=65.0) is None
    assert weather_utils.sanitize_float(-100.0, min_val=-90.0, max_val=65.0) is None
    assert weather_utils.sanitize_float(35.0, min_val=-90.0, max_val=65.0) == 35.0


def test_validate_and_normalize_observation_success():
    """Verify successful transformation into canonical schema."""
    raw = {
        "city": "Bengaluru",
        "timestamp": "2023-04-10T10:00:00",
        "granularity": "hourly",
        "temperature_c": "28.5",
        "relative_humidity_pct": "65",
        "precipitation_mm": "0.5",
        "wind_speed_kmh": "12.0",
        "pressure_msl_hpa": "1012.3",
        "weather_code": "3",
    }
    doc, err = weather_utils.validate_and_normalize_observation(raw)
    assert err is None
    assert doc is not None
    assert doc["city"] == "Bengaluru"
    assert doc["temperature_c"] == 28.5
    assert doc["relative_humidity_pct"] == 65.0
    assert doc["precipitation_mm"] == 0.5
    assert doc["weather_code"] == 3
    assert doc["granularity"] == "hourly"
    assert doc["timestamp"].year == 2023


def test_validate_and_normalize_observation_rejection():
    """Verify rejection of documents missing city or timestamp."""
    # Missing city
    doc, err = weather_utils.validate_and_normalize_observation({"timestamp": "2023-01-01T00:00:00"})
    assert doc is None
    assert "city" in err.lower()

    # Missing/invalid timestamp
    doc, err = weather_utils.validate_and_normalize_observation({"city": "Delhi", "timestamp": "invalid"})
    assert doc is None
    assert "timestamp" in err.lower()


def test_date_range_validation_and_chunking():
    """Verify date range validation and annual chunking logic."""
    start_d, end_d = weather_utils.validate_date_range("2021-01-01", "2023-12-31")
    assert start_d == date(2021, 1, 1)
    assert end_d == date(2023, 12, 31)

    # Inverted date range
    with pytest.raises(ValueError):
        weather_utils.validate_date_range("2023-12-31", "2021-01-01")

    # Chunking 3 years into 365-day slices
    chunks = weather_utils.chunk_date_range(start_d, end_d, max_days=365)
    assert len(chunks) == 3
    assert chunks[0][0] == date(2021, 1, 1)
    assert chunks[-1][1] == date(2023, 12, 31)
