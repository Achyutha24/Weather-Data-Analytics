"""Unit and integration tests for db module.

Tests connection timeout error handling, idempotent bulk upsert logic,
and ingestion run logging.
"""

from datetime import datetime, timezone
import pytest
import mongomock
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

import db
import config


def test_offline_connection_timeout_handling():
    """Verify that attempting to connect to a non-existent port raises ConnectionFailure within timeout."""
    # Connect to an invalid local port with a short 200ms timeout
    client = db.get_mongodb_client(
        uri="mongodb://127.0.0.1:29999/",
        timeout_ms=200,
    )
    with pytest.raises((ConnectionFailure, ServerSelectionTimeoutError)):
        db.ping_server(client)


def test_idempotent_bulk_upsert_logic():
    """Verify that repeating the exact same upsert operation does not create duplicate documents."""
    client = mongomock.MongoClient()
    col = client["test_weather"]["weather_observations"]

    doc1 = {
        "city": "Bengaluru",
        "country": "India",
        "timestamp": datetime(2023, 5, 1, 12, 0, tzinfo=timezone.utc),
        "granularity": "hourly",
        "source": "open_meteo",
        "temperature_c": 28.0,
        "relative_humidity_pct": 50.0,
    }

    # First write
    res1 = db.bulk_upsert_observations([doc1], collection=col)
    assert col.count_documents({}) == 1

    # Second write with same unique identity (city, timestamp, granularity, source)
    doc1_updated = dict(doc1)
    doc1_updated["temperature_c"] = 28.5  # Modified value
    res2 = db.bulk_upsert_observations([doc1_updated], collection=col)

    # Document count should remain 1 (no duplicates!)
    assert col.count_documents({}) == 1
    stored = col.find_one({"city": "Bengaluru"})
    assert stored["temperature_c"] == 28.5


def test_log_and_update_ingestion_run():
    """Verify ingestion run tracking lifecycle in mock collection."""
    client = mongomock.MongoClient()
    runs_col = client["test_weather"]["ingestion_runs"]

    run_record = {
        "run_id": "test_run_123",
        "source": "test_source",
        "status": "in_progress",
        "records_read": 100,
    }
    db.log_ingestion_run(run_record, collection=runs_col)
    assert runs_col.count_documents({}) == 1

    db.update_ingestion_run(
        "test_run_123",
        {"status": "completed", "records_inserted": 100},
        collection=runs_col,
    )
    updated = runs_col.find_one({"run_id": "test_run_123"})
    assert updated["status"] == "completed"
    assert updated["records_inserted"] == 100
