from __future__ import annotations

import logging
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("open-meteo-weather")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


async def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def _resolve_city(city: str) -> dict[str, Any]:
    payload = await _get_json(GEOCODING_URL, {"name": city, "count": 1, "language": "en", "format": "json"})
    results = payload.get("results") or []
    if not results:
        raise ValueError(f"Could not find location: {city}")
    item = results[0]
    return {
        "name": item["name"],
        "country": item.get("country"),
        "latitude": item["latitude"],
        "longitude": item["longitude"],
        "timezone": item.get("timezone", "auto"),
    }


@mcp.tool()
async def get_current_weather(city: str) -> dict[str, Any]:
    """Get the current weather for a city using Open-Meteo."""
    try:
        location = await _resolve_city(city)
        payload = await _get_json(
            FORECAST_URL,
            {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        current = payload["current"]
        return {
            "ok": True,
            "resolved_name": f"{location['name']}, {location.get('country', '')}".strip(", "),
            "temperature_c": current["temperature_2m"],
            "condition": WEATHER_CODES.get(current["weather_code"], "Unknown"),
            "wind_speed_kmh": current["wind_speed_10m"],
            "observed_at": current["time"],
        }
    except Exception as exc:
        logger.exception("get_current_weather failed")
        return {"ok": False, "error": str(exc)}


@mcp.tool()
async def get_weather_forecast(city: str) -> dict[str, Any]:
    """Get tomorrow's weather forecast for a city using Open-Meteo."""
    try:
        location = await _resolve_city(city)
        payload = await _get_json(
            FORECAST_URL,
            {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 2,
                "timezone": "auto",
            },
        )
        daily = payload["daily"]
        index = 1 if len(daily["time"]) > 1 else 0
        weather_code = daily["weather_code"][index]
        return {
            "ok": True,
            "resolved_name": f"{location['name']}, {location.get('country', '')}".strip(", "),
            "date": daily["time"][index],
            "min_temp_c": daily["temperature_2m_min"][index],
            "max_temp_c": daily["temperature_2m_max"][index],
            "rain_probability_percent": daily["precipitation_probability_max"][index],
            "condition": WEATHER_CODES.get(weather_code, "Unknown"),
        }
    except Exception as exc:
        logger.exception("get_weather_forecast failed")
        return {"ok": False, "error": str(exc)}


if __name__ == "__main__":
    mcp.run()
