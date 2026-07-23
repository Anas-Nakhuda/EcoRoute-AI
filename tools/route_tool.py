"""
EcoRoute AI — Route Tool
Geocoding via Open-Meteo (primary) with Nominatim as a fallback, + routing via OSRM.
All three are free, no API key needed.

Why Open-Meteo first: Nominatim's public server aggressively rate-limits and
often 403s requests coming from cloud/shared IPs (Streamlit Cloud, most VPS,
even some home ISPs get blocked). Open-Meteo's geocoder has no such
restriction and is a drop-in replacement for city/place lookups.
"""

from typing import Optional

import requests

from config import NOMINATIM_BASE_URL, OSRM_BASE_URL

HEADERS = {
    # Nominatim requires a descriptive User-Agent per its usage policy.
    "User-Agent": "EcoRouteAI/1.0 (contact: student-project@example.com)"
}

OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

REQUEST_TIMEOUT = 15


def _geocode_open_meteo(place_name: str) -> Optional[dict]:
    """Try Open-Meteo's geocoder first (no key, no rate-limit issues)."""
    try:
        response = requests.get(
            OPEN_METEO_GEOCODE_URL,
            params={"name": place_name.strip(), "count": 1, "language": "en", "format": "json"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return None

    results = data.get("results") or []
    if not results:
        return None

    top = results[0]
    parts = [top.get("name"), top.get("admin1"), top.get("country")]
    display_name = ", ".join(p for p in parts if p)
    return {
        "lat": float(top["latitude"]),
        "lon": float(top["longitude"]),
        "display_name": display_name or place_name,
    }


def _geocode_nominatim(place_name: str) -> Optional[dict]:
    """Fallback: Nominatim (OpenStreetMap)."""
    try:
        response = requests.get(
            f"{NOMINATIM_BASE_URL}/search",
            params={"q": place_name.strip(), "format": "json", "limit": 1, "addressdetails": 1},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
    except requests.RequestException:
        return None

    if not results:
        return None

    top = results[0]
    return {
        "lat": float(top["lat"]),
        "lon": float(top["lon"]),
        "display_name": top.get("display_name", place_name),
    }


def geocode_location(place_name: str) -> dict:
    """
    Convert a place name into coordinates.
    Tries Open-Meteo first, falls back to Nominatim if that fails.
    Raises ValueError if the place cannot be found by either.
    """
    if not place_name or not place_name.strip():
        raise ValueError(place_name)

    result = _geocode_open_meteo(place_name)
    if result is None:
        result = _geocode_nominatim(place_name)

    if result is None:
        raise ValueError(place_name)

    return result


def fetch_route(origin_geo: dict, dest_geo: dict, profile: str = "driving") -> dict:
    """
    Fetch a route between two geocoded points using OSRM.
    Returns distance (km), duration (min), and route geometry (list of [lat, lon]).
    """
    coords = f"{origin_geo['lon']},{origin_geo['lat']};{dest_geo['lon']},{dest_geo['lat']}"
    url = f"{OSRM_BASE_URL}/{profile}/{coords}"
    params = {
        "overview": "full",
        "geometries": "geojson",
    }

    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"OSRM could not find a route (code: {data.get('code', 'unknown')}).")

    route = data["routes"][0]
    # GeoJSON geometry is [lon, lat] pairs — Folium/Leaflet want [lat, lon].
    geometry = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]

    return {
        "distance_km": round(route["distance"] / 1000, 2),
        "duration_min": round(route["duration"] / 60, 1),
        "geometry": geometry,
    }


def fetch_route_complete(origin: str, destination: str, profile: str = "driving") -> dict:
    """
    Full pipeline: geocode both places, then fetch the route between them.
    """
    origin_geo = geocode_location(origin)
    dest_geo = geocode_location(destination)
    route_data = fetch_route(origin_geo, dest_geo, profile=profile)

    return {
        "origin_geo": origin_geo,
        "dest_geo": dest_geo,
        "route_data": route_data,
    }
