"""
EcoRoute AI — Weather Tool
Live weather data via the OpenWeather "Current Weather" API.
"""

import requests

from config import OPENWEATHER_BASE_URL, WEATHER_ICON_URL

REQUEST_TIMEOUT = 15


def fetch_weather(lat: float, lon: float, api_key: str) -> dict:
    """
    Fetch current weather for a coordinate pair.
    Raises requests.HTTPError on bad key / bad request, ValueError if key missing.
    """
    if not api_key:
        raise ValueError("Missing OpenWeather API key.")

    url = f"{OPENWEATHER_BASE_URL}/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }

    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    weather = (data.get("weather") or [{}])[0]
    main = data.get("main", {})
    wind = data.get("wind", {})

    icon = weather.get("icon", "01d")

    return {
        "temp_c": round(main.get("temp", 0), 1),
        "feels_like_c": round(main.get("feels_like", 0), 1),
        "temp_min_c": round(main.get("temp_min", 0), 1),
        "temp_max_c": round(main.get("temp_max", 0), 1),
        "humidity_pct": main.get("humidity", "N/A"),
        "pressure_hpa": main.get("pressure", "N/A"),
        "weather_main": weather.get("main", "Unknown"),
        "weather_desc": weather.get("description", "Unavailable").title(),
        "weather_icon": icon,
        "weather_icon_url": WEATHER_ICON_URL.format(icon=icon),
        "wind_speed_ms": wind.get("speed", "N/A"),
        "wind_deg": wind.get("deg", 0),
        "clouds_pct": data.get("clouds", {}).get("all", "N/A"),
        "visibility_m": data.get("visibility", "N/A"),
        "location_name": data.get("name", "Unknown"),
    }


def get_weather_alert_level(weather: dict) -> dict:
    """
    Classify weather severity into an alert level for the UI badge.
    Returns dict with: level ('good' | 'caution' | 'warning'), message.
    """
    main = str(weather.get("weather_main", "")).lower()
    desc = str(weather.get("weather_desc", "")).lower()
    wind = weather.get("wind_speed_ms", 0)
    try:
        wind = float(wind)
    except (TypeError, ValueError):
        wind = 0

    severe_keywords = ["storm", "tornado", "hurricane", "heavy", "extreme", "squall", "hail"]
    moderate_keywords = ["rain", "snow", "fog", "mist", "thunderstorm", "drizzle", "haze", "smoke"]

    if any(k in main for k in severe_keywords) or any(k in desc for k in severe_keywords) or wind > 15:
        return {"level": "warning", "message": f"⚠️ Severe conditions: {weather.get('weather_desc', 'N/A')}"}
    if any(k in main for k in moderate_keywords) or any(k in desc for k in moderate_keywords) or wind > 8:
        return {"level": "caution", "message": f"⚡ Caution: {weather.get('weather_desc', 'N/A')}"}
    return {"level": "good", "message": f"✅ Good conditions: {weather.get('weather_desc', 'N/A')}"}
