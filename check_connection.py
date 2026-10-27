#!/usr/bin/env python3
"""MongoDB Connection Verification Script.

Verifies that the local MongoDB Community Server is installed, running, and reachable.
Initializes database collections and indexes if the server is available.
Explains the clear distinction between MongoDB Community Server and MongoDB Compass.
"""

import sys
import config
import db
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


def print_banner() -> None:
    print("=" * 70)
    print("   WEATHER ANALYTICS - LOCAL MONGODB CONNECTION CHECK")
    print("=" * 70)


def print_distinction_notice() -> None:
    print("\n[NOTE] IMPORTANT ARCHITECTURE DISTINCTION:")
    print("  * MongoDB Community Server: The background database engine that")
    print("    stores weather data locally on your disk. Listens on 127.0.0.1:27017.")
    print("    It MUST be running for the application to access data.")
    print("  * MongoDB Compass: A graphical user interface (GUI) to view data.")
    print("    Compass connects to Community Server; it DOES NOT replace it.")
    print("    Opening Compass does NOT start the database engine.")
    print("=" * 70)


def print_troubleshooting_guide(err: Exception) -> None:
    print("\n" + "!" * 70)
    print("   CONNECTION FAILED: Local MongoDB Community Server is unreachable!")
    print("!" * 70)
    print(f"\nTarget URI:     {config.MONGODB_URI}")
    print(f"Error Details:  {err}")
    print("\nHOW TO RESOLVE ON WINDOWS:")
    print("1. Check if MongoDB Windows Service is installed and running:")
    print("   Open PowerShell as Administrator and run:")
    print("       Get-Service MongoDB")
    print("")
    print("2. If the service is Stopped, start it by running:")
    print("       Start-Service MongoDB")
    print("")
    print("3. If the service cannot be found:")
    print("   MongoDB Community Server is not installed or was installed without")
    print("   the default Windows Service option.")
    print("   Download and install MongoDB Community Server MSI from:")
    print("       https://www.mongodb.com/try/download/community")
    print("   During installation, ensure 'Install MongoDB as a Service' is checked.")
    print("")
    print("4. REMINDER:")
    print("   Do NOT launch MongoDB Compass expecting it to start the server.")
    print("   MongoDB Compass is only a GUI viewer, not the database engine itself.")
    print("=" * 70)


def main() -> int:
    print_banner()
    print_distinction_notice()
    print(f"Testing connection to: {config.MONGODB_URI}")
    print(f"Connection timeout:    {config.MONGODB_CONNECT_TIMEOUT_MS} ms")
    print("Attempting ping...")

    try:
        client = db.get_mongodb_client()
        server_info = db.ping_server(client)
        print("\n[SUCCESS] Local MongoDB Community Server is connected and active!")
        print(f"  * Server Version:    {server_info.get('version')}")
        print(f"  * Host Address:      {server_info.get('address')}")
        print(f"  * Target Database:   {config.MONGODB_DATABASE}")

        # Initialize collections and indexes safely
        print("\nVerifying / Initializing database collections and indexes...")
        app_db = db.get_database(client)
        indexes = db.init_db_indexes(app_db)
        for col_name, created_idx in indexes.items():
            print(f"  * Collection '{col_name}': {len(created_idx)} index(es) verified/created.")

        print("\n[READY] Your local MongoDB database is fully prepared for weather analytics!")
        print("You can now run data ingestion or launch the Streamlit dashboard:")
        print("  1. python weather_fetcher.py --cities Bengaluru Delhi --start-date 2023-01-01 --end-date 2023-12-31")
        print("  2. streamlit run app.py")
        print("=" * 70)
        return 0

    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        print_troubleshooting_guide(exc)
        return 1
    except Exception as exc:
        print(f"\n[ERROR] An unexpected error occurred: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
