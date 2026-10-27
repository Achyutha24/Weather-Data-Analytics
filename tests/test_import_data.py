"""Unit tests for import_data module.

Tests flexible column mappings, missing value preservation, rejection of malformed rows,
and chunked CSV file processing in dry-run mode.
"""

import os
import tempfile
import pytest
import pandas as pd
import import_data
import config


def test_resolve_row_fields_with_synonyms():
    """Verify that columns with different naming variations map correctly."""
    row = {
        "Datetime": "2023-03-01 15:00:00",
        "Location": "Chennai",
        "Temp": "31.2",
        "Rel_Humidity": "72",
        "Rainfall": "1.4",
        "WindSpeed": "18.5",
        "Pressure": "1010.5",
    }
    doc, err = import_data.resolve_row_fields(row, import_data.DEFAULT_COLUMN_MAPPINGS)
    assert err is None
    assert doc is not None
    assert doc["city"] == "Chennai"
    assert doc["temperature_c"] == 31.2
    assert doc["relative_humidity_pct"] == 72.0
    assert doc["precipitation_mm"] == 1.4
    assert doc["wind_speed_kmh"] == 18.5
    assert doc["pressure_msl_hpa"] == 1010.5


def test_resolve_row_fields_with_default_city():
    """Verify default city fallback when CSV lacks city column."""
    row = {
        "date": "2023-01-01 12:00:00",
        "temp": "24.0",
        "humidity": "50",
    }
    doc, err = import_data.resolve_row_fields(
        row,
        import_data.DEFAULT_COLUMN_MAPPINGS,
        default_city="Bengaluru",
    )
    assert err is None
    assert doc is not None
    assert doc["city"] == "Bengaluru"
    assert doc["latitude"] == config.CITY_REGISTRY["Bengaluru"]["latitude"]


def test_resolve_row_fields_rejection():
    """Verify row is rejected when timestamp is missing or city is absent."""
    # Missing timestamp
    row = {"city": "Delhi", "temp": "25.0"}
    doc, err = import_data.resolve_row_fields(row, import_data.DEFAULT_COLUMN_MAPPINGS)
    assert doc is None
    assert "timestamp" in err.lower()

    # Missing city
    row2 = {"date": "2023-01-01 12:00:00", "temp": "25.0"}
    doc2, err2 = import_data.resolve_row_fields(row2, import_data.DEFAULT_COLUMN_MAPPINGS, default_city=None)
    assert doc2 is None
    assert "city" in err2.lower()


def test_chunked_csv_import_dry_run():
    """Verify incremental chunk processing and statistics reporting in dry-run mode."""
    # Create sample CSV with 5 valid rows and 2 invalid rows
    csv_content = """date,city,temp,humidity,precip
2023-01-01 01:00:00,Delhi,18.5,70,0.0
2023-01-01 02:00:00,Delhi,17.8,72,0.0
2023-01-01 03:00:00,Delhi,17.2,75,0.0
invalid-date,Delhi,16.5,78,0.0
2023-01-01 05:00:00,,16.0,80,0.0
2023-01-01 06:00:00,Delhi,15.8,82,0.0
2023-01-01 07:00:00,Delhi,16.2,80,0.0
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write(csv_content)
        tmp_path = tmp.name

    try:
        summary = import_data.import_csv_file(
            file_path=tmp_path,
            chunk_size=3,  # Force multiple chunks
            dry_run=True,
        )
        assert summary["total_read"] == 7
        assert summary["accepted"] == 5
        assert summary["rejected"] == 2
        assert summary["status"] == "completed"
        assert len(summary["rejection_reasons"]) > 0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
