"""Configuration module for Weather Analytics application.

Handles environment variables, default settings, database connection parameters,
Indian cities registry, and weather API metadata.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Database configuration
MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "weather_analytics")
MONGODB_CONNECT_TIMEOUT_MS: int = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000"))
MONGODB_BATCH_SIZE: int = int(os.getenv("MONGODB_BATCH_SIZE", "1000"))

# Collection names
COLLECTION_WEATHER_OBSERVATIONS = "weather_observations"
COLLECTION_INGESTION_RUNS = "ingestion_runs"

# Open-Meteo Historical Weather API endpoint
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Open-Meteo Hourly API parameter variables mapped to canonical document fields
API_HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
    "cloud_cover",
    "weather_code",
]

API_FIELD_MAPPING: Dict[str, str] = {
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "relative_humidity_pct",
    "precipitation": "precipitation_mm",
    "wind_speed_10m": "wind_speed_kmh",
    "wind_direction_10m": "wind_direction_deg",
    "surface_pressure": "pressure_msl_hpa",
    "cloud_cover": "cloud_cover_pct",
    "weather_code": "weather_code",
}

# Configurable registry for Indian cities
CITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "Bengaluru": {
        "city": "Bengaluru",
        "aliases": ["bengaluru", "bangalore"],
        "country": "India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timezone": "Asia/Kolkata",
    },
    "Hyderabad": {
        "city": "Hyderabad",
        "aliases": ["hyderabad"],
        "country": "India",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "timezone": "Asia/Kolkata",
    },
    "Chennai": {
        "city": "Chennai",
        "aliases": ["chennai", "madras"],
        "country": "India",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "timezone": "Asia/Kolkata",
    },
    "Mumbai": {
        "city": "Mumbai",
        "aliases": ["mumbai", "bombay"],
        "country": "India",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "timezone": "Asia/Kolkata",
    },
    "Delhi": {
        "city": "Delhi",
        "aliases": ["delhi", "new delhi"],
        "country": "India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "Asia/Kolkata",
    },
    "Kolkata": {
        "city": "Kolkata",
        "aliases": ["kolkata", "calcutta"],
        "country": "India",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "timezone": "Asia/Kolkata",
    },
    "Pune": {
        "city": "Pune",
        "aliases": ["pune", "poona"],
        "country": "India",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "timezone": "Asia/Kolkata",
    },
    "Ahmedabad": {
        "city": "Ahmedabad",
        "aliases": ["ahmedabad", "ahmadabad"],
        "country": "India",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "timezone": "Asia/Kolkata",
    },
    "Jaipur": {
        "city": "Jaipur",
        "aliases": ["jaipur"],
        "country": "India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone": "Asia/Kolkata",
    },
    "Kochi": {
        "city": "Kochi",
        "aliases": ["kochi", "cochin"],
        "country": "India",
        "latitude": 9.9312,
        "longitude": 76.2673,
        "timezone": "Asia/Kolkata",
    },
}

# WMO Weather Interpretation Codes (WW)
WMO_CODE_MAP: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_city_metadata(name: str) -> Optional[Dict[str, Any]]:
    """Lookup city metadata from the registry by exact name or alias.

    Args:
        name: Name of city to resolve (case-insensitive).

    Returns:
        Dict with city, country, latitude, longitude, timezone, or None if unknown.
    """
    if not name:
        return None
    cleaned = name.strip().lower()
    for canonical_name, data in CITY_REGISTRY.items():
        if cleaned == canonical_name.lower() or cleaned in data.get("aliases", []):
            return {
                "city": data["city"],
                "country": data["country"],
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "timezone": data["timezone"],
            }
    return None


def get_wmo_description(code: Optional[int]) -> str:
    """Return descriptive string for a WMO weather code."""
    if code is None:
        return "Unknown"
    return WMO_CODE_MAP.get(int(code), f"Weather Code {code}")
