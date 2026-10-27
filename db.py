"""Database management module for local MongoDB operations.

Handles MongoClient lifecycle, server verification, collection indexing,
safe idempotent bulk upserts, and ingestion run logging.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import pymongo
from pymongo import MongoClient, UpdateOne, IndexModel, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, BulkWriteError

import config

logger = logging.getLogger(__name__)


def get_mongodb_client(
    uri: Optional[str] = None,
    timeout_ms: Optional[int] = None,
) -> MongoClient:
    """Create and return a PyMongo MongoClient targeting local MongoDB.

    Args:
        uri: MongoDB connection string (defaults to config.MONGODB_URI).
        timeout_ms: Server selection timeout in milliseconds.

    Returns:
        Configured MongoClient instance.
    """
    connection_uri = uri or config.MONGODB_URI
    timeout = timeout_ms if timeout_ms is not None else config.MONGODB_CONNECT_TIMEOUT_MS

    return MongoClient(
        connection_uri,
        serverSelectionTimeoutMS=timeout,
        connectTimeoutMS=timeout,
        socketTimeoutMS=timeout * 2,
        appname="weather_bigdata_analytics",
    )


def get_database(
    client: Optional[MongoClient] = None,
    db_name: Optional[str] = None,
) -> Database:
    """Return the application's MongoDB database instance."""
    cli = client or get_mongodb_client()
    name = db_name or config.MONGODB_DATABASE
    return cli[name]


def get_collection(
    collection_name: str,
    client: Optional[MongoClient] = None,
    db_name: Optional[str] = None,
) -> Collection:
    """Return a handle to a specific collection within the application database."""
    db = get_database(client=client, db_name=db_name)
    return db[collection_name]


def ping_server(client: Optional[MongoClient] = None) -> Dict[str, Any]:
    """Test connectivity to the local MongoDB server and retrieve server metadata.

    Returns:
        Dict containing server status, version, connection host, and port.

    Raises:
        ConnectionFailure: When the server is unreachable or offline.
    """
    cli = client or get_mongodb_client()
    try:
        # Run a quick ping command
        cli.admin.command("ping")
        # Retrieve server information
        build_info = cli.server_info()
        return {
            "status": "connected",
            "version": build_info.get("version", "Unknown"),
            "git_version": build_info.get("gitVersion", "Unknown"),
            "address": cli.address,
            "max_wire_version": build_info.get("maxWireVersion"),
        }
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        raise ConnectionFailure(
            f"Unable to connect to MongoDB server at {cli.nodes or config.MONGODB_URI}. "
            f"Details: {exc}"
        ) from exc


def init_db_indexes(db: Optional[Database] = None) -> Dict[str, List[str]]:
    """Create necessary performance and uniqueness indexes safely on local collections.

    Returns:
        Dict mapping collection names to lists of created index names.
    """
    database = db if db is not None else get_database()
    results: Dict[str, List[str]] = {}

    # 1. weather_observations indexes
    obs_col = database[config.COLLECTION_WEATHER_OBSERVATIONS]
    obs_indexes = [
        # Compound unique index for idempotent upserts
        IndexModel(
            [
                ("city", ASCENDING),
                ("timestamp", ASCENDING),
                ("granularity", ASCENDING),
                ("source", ASCENDING),
            ],
            unique=True,
            name="uniq_city_ts_gran_source",
        ),
        # Timestamp index for time-range filtering
        IndexModel([("timestamp", ASCENDING)], name="idx_timestamp_asc"),
        # Compound index for city + time queries
        IndexModel([("city", ASCENDING), ("timestamp", ASCENDING)], name="idx_city_timestamp"),
        # Granularity index
        IndexModel([("granularity", ASCENDING)], name="idx_granularity"),
    ]

    try:
        created_obs = obs_col.create_indexes(obs_indexes)
        results[config.COLLECTION_WEATHER_OBSERVATIONS] = created_obs
    except Exception as exc:
        logger.error("Failed to create indexes on %s: %s", config.COLLECTION_WEATHER_OBSERVATIONS, exc)
        raise

    # 2. ingestion_runs indexes
    runs_col = database[config.COLLECTION_INGESTION_RUNS]
    run_indexes = [
        IndexModel([("run_id", ASCENDING)], unique=True, name="uniq_run_id"),
        IndexModel([("start_time", DESCENDING)], name="idx_runs_start_time_desc"),
    ]
    try:
        created_runs = runs_col.create_indexes(run_indexes)
        results[config.COLLECTION_INGESTION_RUNS] = created_runs
    except Exception as exc:
        logger.error("Failed to create indexes on %s: %s", config.COLLECTION_INGESTION_RUNS, exc)
        raise

    return results


def bulk_upsert_observations(
    observations: List[Dict[str, Any]],
    collection: Optional[Collection] = None,
    batch_size: Optional[int] = None,
) -> Dict[str, int]:
    """Perform batched, idempotent upserts of normalized weather observation documents.

    Uses MongoDB UpdateOne operations with upsert=True, matched by (city, timestamp,
    granularity, source). Repeating the same ingestion does not generate duplicate records.

    Args:
        observations: List of canonical weather observation documents.
        collection: Optional Collection handle (defaults to weather_observations).
        batch_size: Batch write chunk size.

    Returns:
        Dict with total, inserted, updated, and matched record counts.
    """
    if not observations:
        return {"total": 0, "inserted": 0, "updated": 0, "matched": 0}

    col = collection if collection is not None else get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)
    size = batch_size or config.MONGODB_BATCH_SIZE

    total_inserted = 0
    total_updated = 0
    total_matched = 0

    operations: List[UpdateOne] = []
    for doc in observations:
        filter_spec = {
            "city": doc["city"],
            "timestamp": doc["timestamp"],
            "granularity": doc["granularity"],
            "source": doc["source"],
        }
        # Update fields with $set, setting ingested_at on insert
        operations.append(
            UpdateOne(
                filter_spec,
                {
                    "$set": doc,
                    "$setOnInsert": {"first_ingested_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
        )

        if len(operations) >= size:
            try:
                res = col.bulk_write(operations, ordered=False)
                total_inserted += res.upserted_count
                total_updated += res.modified_count
                total_matched += res.matched_count
            except BulkWriteError as bwe:
                logger.error("Bulk write error: %s", bwe.details)
                # Count partial successes
                total_inserted += bwe.details.get("nUpserted", 0)
                total_updated += bwe.details.get("nModified", 0)
                total_matched += bwe.details.get("nMatched", 0)
            operations = []

    # Write remaining operations
    if operations:
        try:
            res = col.bulk_write(operations, ordered=False)
            total_inserted += res.upserted_count
            total_updated += res.modified_count
            total_matched += res.matched_count
        except BulkWriteError as bwe:
            logger.error("Bulk write error on remaining batch: %s", bwe.details)
            total_inserted += bwe.details.get("nUpserted", 0)
            total_updated += bwe.details.get("nModified", 0)
            total_matched += bwe.details.get("nMatched", 0)

    return {
        "total": len(observations),
        "inserted": total_inserted,
        "updated": total_updated,
        "matched": total_matched,
    }


def log_ingestion_run(
    run_doc: Dict[str, Any],
    collection: Optional[Collection] = None,
) -> str:
    """Insert an ingestion run record into the ingestion_runs collection."""
    col = collection if collection is not None else get_collection(config.COLLECTION_INGESTION_RUNS)
    col.insert_one(run_doc)
    return str(run_doc.get("run_id"))


def update_ingestion_run(
    run_id: str,
    update_fields: Dict[str, Any],
    collection: Optional[Collection] = None,
) -> None:
    """Update an existing ingestion run record by its unique run_id."""
    col = collection if collection is not None else get_collection(config.COLLECTION_INGESTION_RUNS)
    col.update_one({"run_id": run_id}, {"$set": update_fields})
