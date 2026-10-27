"""Utility module for weather data normalization, validation, and parsing.

Provides robust timestamp normalization to UTC BSON datetimes, numeric sanitization,
physical range validation, date-range chunking, and document identity generation.
"""

from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import math
import re


# Physical bounds for meteorological sanity checks
METEOROLOGICAL_BOUNDS = {
    "temperature_c": (-90.0, 65.0),
    "relative_humidity_pct": (0.0, 100.0),
    "precipitation_mm": (0.0, 1000.0),
    "wind_speed_kmh": (0.0, 450.0),
    "wind_direction_deg": (0.0, 360.0),
    "pressure_msl_hpa": (850.0, 1100.0),
    "cloud_cover_pct": (0.0, 100.0),
    "weather_code": (0, 99),
}


def parse_timestamp(value: Any, default_tz: timezone = timezone.utc) -> Optional[datetime]:
    """Parse various timestamp representations into a timezone-aware UTC datetime.

    Supports:
        - datetime objects (naive or aware)
        - date objects
        - ISO format strings (e.g. "2023-01-01T12:00:00", "2023-01-01 12:00:00Z")
        - Common date strings (e.g. "2023-01-01", "01/01/2023", "01-01-2023")
        - Unix timestamps (int/float seconds or milliseconds)

    Returns:
        datetime in UTC, or None if parsing fails.
    """
    if value is None:
        return None

    # Handle pandas NaT or float NaN
    if isinstance(value, float) and math.isnan(value):
        return None

    if str(value).strip().lower() in ("", "nat", "nan", "null", "none"):
        return None

    # Already a datetime
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=default_tz).astimezone(timezone.utc)
        return value.astimezone(timezone.utc)

    # Date object
    if isinstance(value, date):
        dt = datetime.combine(value, datetime.min.time())
        return dt.replace(tzinfo=default_tz).astimezone(timezone.utc)

    # Numeric Unix epoch timestamp
    if isinstance(value, (int, float)):
        try:
            # If timestamp is > 1e11, it's likely milliseconds
            if value > 1e11:
                return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None

    # String parsing
    str_val = str(value).strip()
    if not str_val:
        return None

    # Replace space with T for standard ISO format if needed
    cleaned_str = str_val.replace("Z", "+00:00")

    # Common formats to attempt
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
    ]

    # Try fromisoformat first (Python 3.11+ supports most ISO variants)
    try:
        dt = datetime.fromisoformat(cleaned_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=default_tz).astimezone(timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned_str, fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=default_tz).astimezone(timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    return None


def sanitize_float(
    value: Any,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    decimals: Optional[int] = 2,
) -> Optional[float]:
    """Convert an arbitrary value to a float or None without inventing values.

    Args:
        value: Input value to convert.
        min_val: Optional minimum valid threshold.
        max_val: Optional maximum valid threshold.
        decimals: Number of decimal places to round to (None preserves raw float).

    Returns:
        Sanitized float within range, or None.
    """
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        if not v or v.lower() in ("nan", "null", "none", "na", "n/a", "-", "--"):
            return None
        # Remove non-numeric characters except digits, minus sign, and dot
        cleaned = re.sub(r"[^\d.-]", "", v)
        if not cleaned or cleaned in ("-", "."):
            return None
        try:
            f_val = float(cleaned)
        except ValueError:
            return None
    else:
        try:
            f_val = float(value)
        except (ValueError, TypeError):
            return None

    if math.isnan(f_val) or math.isinf(f_val):
        return None

    if min_val is not None and f_val < min_val:
        return None
    if max_val is not None and f_val > max_val:
        return None

    if decimals is not None:
        return round(f_val, decimals)
    return f_val


def sanitize_int(value: Any, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Optional[int]:
    """Convert an arbitrary value to an integer or None."""
    f = sanitize_float(value, min_val=float(min_val) if min_val is not None else None,
                               max_val=float(max_val) if max_val is not None else None,
                               decimals=None)
    if f is None:
        return None
    return int(round(f))


def validate_and_normalize_observation(
    raw: Dict[str, Any],
    default_source: str = "open_meteo",
    default_granularity: str = "hourly",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Validate a raw observation dictionary and transform into canonical schema.

    Returns:
        Tuple of (canonical_doc, error_message). If invalid, canonical_doc is None.
    """
    city = str(raw.get("city", "")).strip()
    if not city:
        return None, "Missing required field: city"

    raw_ts = raw.get("timestamp")
    ts = parse_timestamp(raw_ts)
    if ts is None:
        return None, f"Invalid or missing timestamp: '{raw_ts}'"

    granularity = str(raw.get("granularity") or default_granularity).strip().lower()
    if granularity not in ("hourly", "daily"):
        granularity = default_granularity

    source = str(raw.get("source") or default_source).strip().lower()

    # Sanitize meteorological values
    temp_c = sanitize_float(
        raw.get("temperature_c"),
        min_val=METEOROLOGICAL_BOUNDS["temperature_c"][0],
        max_val=METEOROLOGICAL_BOUNDS["temperature_c"][1],
        decimals=2,
    )
    humidity = sanitize_float(
        raw.get("relative_humidity_pct"),
        min_val=METEOROLOGICAL_BOUNDS["relative_humidity_pct"][0],
        max_val=METEOROLOGICAL_BOUNDS["relative_humidity_pct"][1],
        decimals=2,
    )
    precipitation = sanitize_float(
        raw.get("precipitation_mm"),
        min_val=METEOROLOGICAL_BOUNDS["precipitation_mm"][0],
        max_val=METEOROLOGICAL_BOUNDS["precipitation_mm"][1],
        decimals=2,
    )
    wind_speed = sanitize_float(
        raw.get("wind_speed_kmh"),
        min_val=METEOROLOGICAL_BOUNDS["wind_speed_kmh"][0],
        max_val=METEOROLOGICAL_BOUNDS["wind_speed_kmh"][1],
        decimals=2,
    )
    wind_dir = sanitize_float(
        raw.get("wind_direction_deg"),
        min_val=METEOROLOGICAL_BOUNDS["wind_direction_deg"][0],
        max_val=METEOROLOGICAL_BOUNDS["wind_direction_deg"][1],
        decimals=2,
    )
    pressure = sanitize_float(
        raw.get("pressure_msl_hpa"),
        min_val=METEOROLOGICAL_BOUNDS["pressure_msl_hpa"][0],
        max_val=METEOROLOGICAL_BOUNDS["pressure_msl_hpa"][1],
        decimals=2,
    )
    cloud_cover = sanitize_float(
        raw.get("cloud_cover_pct"),
        min_val=METEOROLOGICAL_BOUNDS["cloud_cover_pct"][0],
        max_val=METEOROLOGICAL_BOUNDS["cloud_cover_pct"][1],
        decimals=2,
    )
    weather_code = sanitize_int(
        raw.get("weather_code"),
        min_val=METEOROLOGICAL_BOUNDS["weather_code"][0],
        max_val=METEOROLOGICAL_BOUNDS["weather_code"][1],
    )

    doc: Dict[str, Any] = {
        "city": city,
        "country": raw.get("country", "India"),
        "latitude": sanitize_float(raw.get("latitude"), decimals=4),
        "longitude": sanitize_float(raw.get("longitude"), decimals=4),
        "timezone": raw.get("timezone", "Asia/Kolkata"),
        "timestamp": ts,
        "granularity": granularity,
        "temperature_c": temp_c,
        "relative_humidity_pct": humidity,
        "precipitation_mm": precipitation,
        "wind_speed_kmh": wind_speed,
        "wind_direction_deg": wind_dir,
        "pressure_msl_hpa": pressure,
        "cloud_cover_pct": cloud_cover,
        "weather_code": weather_code,
        "source": source,
        "ingested_at": datetime.now(timezone.utc),
    }

    return doc, None


def generate_document_filter(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the unique query filter for idempotent MongoDB upserts."""
    return {
        "city": doc["city"],
        "timestamp": doc["timestamp"],
        "granularity": doc["granularity"],
        "source": doc["source"],
    }


def validate_date_range(start_date_str: str, end_date_str: str) -> Tuple[date, date]:
    """Validate and parse start and end date strings (YYYY-MM-DD).

    Raises:
        ValueError if date format is invalid or start_date > end_date.
    """
    try:
        start_d = datetime.strptime(start_date_str.strip(), "%Y-%m-%d").date()
    except Exception as e:
        raise ValueError(f"Invalid start_date '{start_date_str}': Expected YYYY-MM-DD. Error: {e}")

    try:
        end_d = datetime.strptime(end_date_str.strip(), "%Y-%m-%d").date()
    except Exception as e:
        raise ValueError(f"Invalid end_date '{end_date_str}': Expected YYYY-MM-DD. Error: {e}")

    if start_d > end_d:
        raise ValueError(f"start_date ({start_d}) cannot be after end_date ({end_d})")

    return start_d, end_d


def chunk_date_range(start_d: date, end_d: date, max_days: int = 365) -> List[Tuple[date, date]]:
    """Split a wide date range into bounded slices to prevent API request timeouts.

    Args:
        start_d: Start date.
        end_d: End date.
        max_days: Maximum duration in days for each chunk (default: 365 days / 1 year).

    Returns:
        List of (chunk_start, chunk_end) date pairs.
    """
    chunks = []
    current_start = start_d
    while current_start <= end_d:
        current_end = min(current_start + timedelta(days=max_days - 1), end_d)
        chunks.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    return chunks
