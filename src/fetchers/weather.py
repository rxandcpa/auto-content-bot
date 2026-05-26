"""Fetch weather data. Uses OpenWeatherMap if key is set, otherwise wttr.in (free)."""

from __future__ import annotations

import logging
import requests

import src.config as config

logger = logging.getLogger(__name__)


def fetch_weather(city_name: str, lat: float, lon: float) -> dict:
    """Fetch weather for one city. Returns dict with weather info or error."""
    api_key = config.OPENWEATHER_API_KEY
    if api_key:
        return _fetch_owm(city_name, lat, lon, api_key)
    return _fetch_wttr(city_name)


def _fetch_owm(city_name: str, lat: float, lon: float, api_key: str) -> dict:
    """OpenWeatherMap One Call API (free tier: 1000 calls/day)."""
    try:
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "exclude": "minutely,hourly,alerts",
            "lang": "zh_cn",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        daily = data.get("daily", [{}])[0]
        return {
            "city": city_name,
            "temp": current.get("temp", "N/A"),
            "description": current.get("weather", [{}])[0].get("description", ""),
            "humidity": current.get("humidity", "N/A"),
            "daily_high": daily.get("temp", {}).get("max", "N/A"),
            "daily_low": daily.get("temp", {}).get("min", "N/A"),
            "success": True,
        }
    except Exception as e:
        logger.warning(f"OWM fetch failed for {city_name}: {e}")
        return _fetch_wttr(city_name)


def _fetch_wttr(city_name: str) -> dict:
    """Fallback using wttr.in (free, no key needed)."""
    try:
        url = f"https://wttr.in/{city_name}?format=j1"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current_condition", [{}])[0]
        weather = data.get("weather", [{}])[0]
        return {
            "city": city_name,
            "temp": current.get("temp_C", "N/A"),
            "description": current.get("weatherDesc", [{}])[0].get("value", ""),
            "humidity": current.get("humidity", "N/A"),
            "daily_high": weather.get("maxtempC", "N/A"),
            "daily_low": weather.get("mintempC", "N/A"),
            "success": True,
        }
    except Exception as e:
        logger.error(f"wttr.in fetch failed for {city_name}: {e}")
        return {"city": city_name, "success": False}


def fetch_all_weather() -> list[dict]:
    """Fetch weather for all configured cities."""
    results = []
    for name, lat, lon in config.WEATHER_CITIES:
        logger.info(f"Fetching weather for {name}...")
        data = fetch_weather(name, lat, lon)
        results.append(data)
    return results


def format_weather_data(cities: list[dict]) -> str:
    """Convert weather data list into a text summary."""
    lines = []
    for c in cities:
        if c.get("success"):
            lines.append(
                f"{c['city']}: {c['description']}, 当前{c['temp']}°C, "
                f"最高{c['daily_high']}°C / 最低{c['daily_low']}°C, "
                f"湿度{c['humidity']}%"
            )
        else:
            lines.append(f"{c['city']}: 暂无数据")
    return "\n".join(lines)
