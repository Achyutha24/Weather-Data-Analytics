# Weather Data Storage and Analysis Using MongoDB for Big Data Processing

A production-grade, end-to-end Big Data weather storage and analytics platform built with **Python**, **local MongoDB Community Server**, **PyMongo**, and **Streamlit**.

This platform retrieves high-resolution historical hourly weather observations (2021–2025) from the **Open-Meteo Historical Weather API**, normalizes and validates meteorological variables, performs idempotent bulk upserts into a local NoSQL database, runs high-performance **MongoDB aggregation pipelines** for big-data analytical queries, and presents real-time interactive visualizations across an 8-page **Streamlit & Plotly** dashboard.

---

## ⚠️ Crucial Architectural Distinction: MongoDB Community Server vs. Compass

Before setting up the project, it is essential to understand the difference between the database engine and the graphical interface:

| Characteristic | **MongoDB Community Server** | **MongoDB Compass** |
| :--- | :--- | :--- |
| **Role** | **Database Engine & Local Disk Storage** | **Graphical User Interface (GUI) Client** |
| **Execution** | Runs as a background Windows service (`mongod.exe`) | Interactive desktop application |
| **Default Port** | Listens on `127.0.0.1:27017` | Connects as a client to `127.0.0.1:27017` |
| **Necessity** | **MANDATORY**: Python scripts cannot read or write data without it | **OPTIONAL**: Helpful for inspecting documents visually |
| **Key Misconception** | Opening Compass **DOES NOT** start the database server | Compass **CANNOT** run queries if Community Server is stopped |

> **IMPORTANT:** Do NOT launch MongoDB Compass expecting it to start the database server. If the MongoDB Community Server service is stopped or not installed, Compass will fail to connect with an error such as `connect ECONNREFUSED 127.0.0.1:27017`.

---

## 📥 Official Download Links

* **MongoDB Community Server (MSI Installer):**  
  [https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)  
  *(Select: Windows x64, Package: MSI)*

* **MongoDB Compass (GUI Viewer):**  
  [https://www.mongodb.com/try/download/compass?platform=windows](https://www.mongodb.com/try/download/compass?platform=windows)  
  *(Select: Windows 64-bit EXE or MSI)*

---

## 🪟 Windows Setup Instructions

### 1. Download & Install MongoDB Community Server
1. Download the `.msi` installer from the [MongoDB Community Download Center](https://www.mongodb.com/try/download/community).
2. Launch the installer and select the **"Complete"** installation type.
3. On the **Service Configuration** screen:
   * Ensure **"Install MongoDB as a Service"** is checked.
   * Choose **"Run service as Network Service user"** (default).
   * Note the Data Directory (`C:\Program Files\MongoDB\Server\X.X\data\`) and Log Directory.
4. (Optional) Check **"Install MongoDB Compass"** if offered during the setup wizard.
5. Click **Install**.

### 2. Verify or Start the Windows Service
Open Windows PowerShell as Administrator and check the service status:
```powershell
Get-Service MongoDB
```

* **If the service status is `Running`:** Your database server is active and ready.
* **If the service status is `Stopped`:** Start it immediately by running:
  ```powershell
  Start-Service MongoDB
  ```
* **If PowerShell returns `Cannot find any service with service name 'MongoDB'`:**
  MongoDB Community Server is either not installed or was installed without the default Windows service option. Please check `C:\Program Files\MongoDB\Server\` or download and run the MSI installer as described above.

---

## 🚀 Step-by-Step Execution Flow

Follow this exact sequence to configure the environment, ingest historical weather data, and launch the interactive analytics dashboard:

### Step 1: Install MongoDB Community Server
Follow the instructions above and ensure the service is running.

### Step 2: Install MongoDB Compass
Install Compass to browse documents and inspect aggregation results visually.

### Step 3: Confirm the Database Service is Running
Open PowerShell:
```powershell
Get-Service MongoDB
```
If stopped:
```powershell
Start-Service MongoDB
```

### Step 4: Create Virtual Environment and Install Dependencies
From the project workspace root (`C:\Users\achyu\Desktop\BDA`):
```powershell
# Create Python virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1
```

> **Tip for PowerShell Script Execution:** If PowerShell displays an execution policy restriction (`running scripts is disabled on this system`), you can activate the environment in Command Prompt (`.venv\Scripts\activate.bat`) or invoke Python directly via `.venv\Scripts\python.exe` without altering system-wide security settings.

Install the required packages:
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Default configuration values in `.env`:
```ini
MONGODB_URI=mongodb://127.0.0.1:27017/
MONGODB_DATABASE=weather_analytics
MONGODB_CONNECT_TIMEOUT_MS=5000
MONGODB_BATCH_SIZE=1000
```

### Step 6: Verify MongoDB Server Connectivity
Run the diagnostic connection check script:
```powershell
python check_connection.py
```
This script will:
* Ping the local MongoDB Community Server.
* Display the server version and connection address.
* Verify and create required collections and compound unique indexes.
* Provide beginner-friendly troubleshooting steps if the server is offline.

### Step 7: Fetch and Ingest Historical Weather Records
Ingest 5 years (2021–2025) of hourly historical observations for Indian cities from the Open-Meteo Historical Archive API:
```powershell
# Ingest all 10 registered Indian cities (2021-01-01 to 2025-12-31)
python weather_fetcher.py --cities all --start-date 2021-01-01 --end-date 2025-12-31

# Or ingest specific cities for a customized date window:
python weather_fetcher.py --cities Bengaluru Delhi Mumbai --start-date 2023-01-01 --end-date 2023-12-31
```
* The fetcher automatically splits multi-year requests into bounded chunks to respect API limits.
* All observations are idempotently upserted into `weather_observations` with full progress reporting.
* Ingestion run metadata is recorded in `ingestion_runs`.

### Step 8: (Optional) Ingest CSV or Kaggle Weather Datasets
You can incrementally ingest external CSV files without memory exhaustion:
```powershell
python import_data.py --file data/sample_weather.csv --city Bengaluru --granularity hourly --source kaggle_csv
```
* **Supported arguments:**
  * `--file` / `-f`: Path to the CSV file (required).
  * `--city`: Default city if the CSV lacks a city/location column.
  * `--granularity`: `hourly` or `daily` (default: `hourly`).
  * `--source`: Source identifier label (default: `kaggle_csv`).
  * `--chunk-size`: Number of rows per pandas chunk (default: `5000`).
  * `--dry-run`: Validate CSV rows without inserting into the database.

### Step 9: Launch the Streamlit Dashboard
Launch the interactive web application:
```powershell
streamlit run app.py
```

### Step 10: Open Dashboard in Browser
Open your web browser and navigate to:
```
http://localhost:8501
```

### Step 11: Inspect Database in MongoDB Compass
1. Open **MongoDB Compass**.
2. Connect to the local server URI:
   ```
   mongodb://127.0.0.1:27017/
   ```
3. Click **Connect**.
4. In the left navigation pane, browse the `weather_analytics` database.
5. Inspect the documents in:
   * `weather_observations` (Canonical weather observations)
   * `ingestion_runs` (Audit trail of ingestion batches)

---

## 🏛️ System Architecture and Data Model

### Database: `weather_analytics`

#### Collection 1: `weather_observations`
Stores individual historical meteorological observations. Each document conforms to the canonical schema:
```json
{
  "city": "Bengaluru",
  "country": "India",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "timezone": "Asia/Kolkata",
  "timestamp": "2023-05-15T10:00:00Z",
  "granularity": "hourly",
  "temperature_c": 27.4,
  "relative_humidity_pct": 68.0,
  "precipitation_mm": 0.2,
  "wind_speed_kmh": 12.5,
  "wind_direction_deg": 180.0,
  "pressure_msl_hpa": 1012.4,
  "cloud_cover_pct": 45.0,
  "weather_code": 3,
  "source": "open_meteo",
  "ingested_at": "2026-10-23T06:55:00Z"
}
```

#### Collection 2: `ingestion_runs`
Maintains an audit trail of all ingestion jobs:
```json
{
  "run_id": "run_20261023_065500_a1b2c3",
  "source": "open_meteo",
  "requested_cities": ["Bengaluru", "Delhi"],
  "requested_date_range": {"start": "2021-01-01", "end": "2025-12-31"},
  "start_time": "2026-10-23T06:55:00Z",
  "finish_time": "2026-10-23T06:57:12Z",
  "status": "completed",
  "records_read": 87600,
  "records_accepted": 87600,
  "records_rejected": 0,
  "records_inserted": 87600,
  "records_updated": 0,
  "duration_seconds": 132.0
}
```

### Database Indexes
* **Compound Unique Index:** `(city: 1, timestamp: 1, granularity: 1, source: 1)` guarantees idempotency. Re-running imports updates existing documents rather than creating duplicates.
* **Timestamp Index:** `(timestamp: 1)` enables sub-millisecond range queries across years.
* **City & Timestamp Compound Index:** `(city: 1, timestamp: 1)` accelerates time-series trend extraction per city.
* **Granularity Index:** `(granularity: 1)` prevents mixing hourly and daily statistics.

---

## 📈 Big Data Aggregation Pipelines (`analytics.py`)

Rather than loading millions of records into pandas in Python memory, all heavy computation is delegated directly to the local MongoDB database engine using aggregation pipelines:

1. **High-Level Statistics (`$facet`):** Computes observation counts, temporal boundaries, thermal extremes, and cumulative precipitation in a single round-trip.
2. **City Temperature Metrics (`$match` $\rightarrow$ `$group` $\rightarrow$ `$project`):** Groups by city to compute minimum, maximum, average temperatures, and temperature spreads.
3. **Daily & Monthly Aggregations (`$dateToString` $\rightarrow$ `$group`):** Truncates datetimes to extract seasonal and diurnal trajectories.
4. **Precipitation & Monsoon Analysis:** Distinguishes recorded zero precipitation (`0.0 mm`) from missing measurements (`null`) and calculates rainy-hour fractions and wettest dates.
5. **Data Quality and Completeness:** Analyzes field-level null frequencies across all meteorological attributes.
6. **Bounded Relationships:** Uses `$sample` and `$project` to pull representative bounded samples for responsive Plotly scatter and correlation matrices without freezing the browser.

---

## 📊 Streamlit Dashboard Modules (`app.py`)

* **Page A: Overview** — KPI scorecards, temperature ranges, cumulative rainfall, temporal coverage, and meteorological insights.
* **Page B: Temperature Trends** — Hourly, daily, and monthly line charts with interactive min-average-max thermal envelopes.
* **Page C: City Comparison** — Multi-city comparative bar charts and box plots across thermal, rainfall, humidity, and wind metrics.
* **Page D: Rainfall Analysis** — Monsoon trajectories, monthly totals, and peak downpour leaderboards.
* **Page E: Wind & Extreme Weather** — User-adjustable wind speed threshold query and historical extreme temperature tables.
* **Page F: Weather Relationships** — Bivariate scatter plots with OLS regression lines and Pearson correlation heatmaps (*with explicit clarification that correlation does not imply causation*).
* **Page G: Data Explorer** — Server-side paginated tabular query browser with filtering by city, date, granularity, and source, plus instant CSV export.
* **Page H: Database & Ingestion** — Live server diagnostics, collection sizes, data completeness reports, and interactive API/CSV ingestion triggers.

---

## 🧪 Automated Testing Suite

The project includes unit and integration tests under `tests/`:

* `tests/test_weather_utils.py`: Timestamp parsing, ISO formatting, numeric range validation, meteorological sanity boundaries, and date-range chunking.
* `tests/test_import_data.py`: Flexible column synonyms, default city fallbacks, malformed row rejections, and chunked CSV processing in dry-run mode.
* `tests/test_analytics.py`: MongoDB aggregation pipeline construction, empty dataset graceful handling, and data quality null detection.
* `tests/test_db.py`: Offline connection failure handling within timeout bounds and idempotent bulk upsert logic.
* `tests/test_weather_fetcher.py`: Open-Meteo payload parsing and mocked API response processing.

To run the complete test suite:
```powershell
.venv\Scripts\python.exe -m pytest -v
```

---

## 📜 Attribution and Licensing

* **Weather Data Source:** [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
* **Reanalysis Model Attribution:** Weather data is derived from the ECMWF ERA5 and ERA5-Land numerical weather reanalysis models combined with station observations.
* **License:** Open-source project built for educational, research, and big-data engineering demonstrations.
