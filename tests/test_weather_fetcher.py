"""Unit tests for weather_fetcher module.

Tests Open-Meteo API response parsing, meteorological field mapping,
and dry-run execution without network or database dependencies.
"""

from datetime import date
from unittest.mock import patch, MagicMock
import pytest

import weather_fetcher
import config


@pytest.fixture
def sample_api_payload():
    """Mock API response payload structured like Open-Meteo historical archive API."""
    return {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timezone": "Asia/Kolkata",
        "hourly": {
            "time": [
                "2023-01-01T00:00",
                "2023-01-01T01:00",
                "2023-01-01T02:00",
            ],
            "temperature_2m": [18.2, 17.5, 17.0],
            "relative_humidity_2m": [75.0, 78.0, 80.0],
            "precipitation": [0.0, 0.0, 0.4],
            "wind_speed_10m": [8.5, 9.0, 11.2],
            "wind_direction_10m": [120.0, 130.0, 140.0],
            "surface_pressure": [1014.5, 1014.2, 1013.9],
            "cloud_cover": [10.0, 20.0, 65.0],
            "weather_code": [0, 1, 61],
        },
    }


def test_parse_open_meteo_payload(sample_api_payload):
    """Verify transformation of API hourly block into canonical observation documents."""
    city_meta = config.get_city_metadata("Bengaluru")
    docs = weather_fetcher.parse_open_meteo_payload(city_meta, sample_api_payload)

    assert len(docs) == 3

    first = docs[0]
    assert first["city"] == "Bengaluru"
    assert first["temperature_c"] == 18.2
    assert first["relative_humidity_pct"] == 75.0
    assert first["precipitation_mm"] == 0.0
    assert first["weather_code"] == 0
    assert first["source"] == "open_meteo"
    assert first["granularity"] == "hourly"

    third = docs[2]
    assert third["precipitation_mm"] == 0.4
    assert third["weather_code"] == 61


def test_fetch_open_meteo_chunk_mock_success(sample_api_payload):
    """Verify HTTP request and retry logic with mocked successful response."""
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_api_payload
        mock_get.return_value = mock_resp

        payload = weather_fetcher.fetch_open_meteo_chunk(
            latitude=12.9716,
            longitude=77.5946,
            timezone_str="Asia/Kolkata",
            start_d=date(2023, 1, 1),
            end_d=date(2023, 1, 1),
        )

        assert payload is not None
        assert "hourly" in payload
        assert len(payload["hourly"]["time"]) == 3
        mock_get.assert_called_once()
