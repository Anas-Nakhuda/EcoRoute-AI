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
import math

import requests

from config import NOMINATIM_BASE_URL, OSRM_BASE_URL

HEADERS = {
    # Nominatim requires a descriptive User-Agent per its usage policy.
    "User-Agent": "EcoRouteAI/1.0 (contact: student-project@example.com)"
}

OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

REQUEST_TIMEOUT = 15


class NoGroundRouteError(Exception):
    """
    Raised when OSRM cannot find ANY road/ferry path between two points —
    meaning they're separated by open water with no mapped crossing (e.g.
    across an ocean). In that case Car/Train/Bike/Walk aren't physically
    possible at all; only Flight is.
    """
    pass


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle ('as the crow flies') distance between two points, in km."""
    R = 6371.0088  # mean Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)), 2)


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
        "country": top.get("country") or "",
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
    address = top.get("address") or {}
    return {
        "lat": float(top["lat"]),
        "lon": float(top["lon"]),
        "display_name": top.get("display_name", place_name),
        "country": address.get("country", "") if isinstance(address, dict) else "",
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
    Returns distance (km), duration (min), route geometry (list of [lat, lon]),
    and ferry-crossing info — OSRM tags individual steps with mode="ferry"
    when the route includes a mapped sea/strait ferry crossing, which is
    the signal used elsewhere to decide whether Train is realistic for
    this route (trains generally don't cross open water).
    """
    coords = f"{origin_geo['lon']},{origin_geo['lat']};{dest_geo['lon']},{dest_geo['lat']}"
    url = f"{OSRM_BASE_URL}/{profile}/{coords}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
    }

    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise NoGroundRouteError(
            f"OSRM could not find a road/ferry path (code: {data.get('code', 'unknown')})."
        )

    route = data["routes"][0]
    # GeoJSON geometry is [lon, lat] pairs — Folium/Leaflet want [lat, lon].
    geometry = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]

    ferry_m = 0.0
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            if step.get("mode") == "ferry":
                ferry_m += step.get("distance", 0)

    return {
        "distance_km": round(route["distance"] / 1000, 2),
        "duration_min": round(route["duration"] / 60, 1),
        "geometry": geometry,
        "ferry_km": round(ferry_m / 1000, 2),
        "has_ferry": ferry_m > 0,
    }


def fetch_route_complete(origin: str, destination: str, profile: str = "driving") -> dict:
    """
    Full pipeline: geocode both places, then fetch the route between them.

    `route_data` will be None if OSRM cannot find any road/ferry path at all
    (e.g. the two places are separated by open ocean with no mapped
    crossing) — the caller should treat that as "only Flight is possible".
    `great_circle_km` is always returned (pure math, no network round trip
    the OSRM call already didn't need) so Flight distance can be computed
    even when ground routing fails entirely.
    """
    origin_geo = geocode_location(origin)
    dest_geo = geocode_location(destination)

    great_circle_km = _haversine_km(
        origin_geo["lat"], origin_geo["lon"], dest_geo["lat"], dest_geo["lon"]
    )

    try:
        route_data = fetch_route(origin_geo, dest_geo, profile=profile)
    except NoGroundRouteError:
        route_data = None

    return {
        "origin_geo": origin_geo,
        "dest_geo": dest_geo,
        "route_data": route_data,
        "great_circle_km": great_circle_km,
    }


def check_mode_feasibility(
    mode_cfg: dict,
    route_data: Optional[dict],
    great_circle_km: float,
    origin_country: str = "",
    dest_country: str = "",
):
    """
    Decide whether the selected travel mode is actually possible for this
    route — not just "unrealistic" (see max/min_realistic_km in config.py
    for that), but physically impossible.

    Returns (feasible: bool, reason: str | None).
    """
    kind = mode_cfg.get("kind", "road")

    if kind == "flight":
        return True, None

    if route_data is None:
        return False, (
            "No road or ferry connection exists between these two places — "
            "they're separated by open water with no mapped crossing. "
            "✈️ Flight is the only realistic option for this route."
        )

    if kind == "rail":
        if route_data.get("has_ferry"):
            return False, (
                f"This route requires a ~{route_data['ferry_km']} km sea ferry crossing. "
                "No direct train service crosses open water like this — try 🚗 Car "
                "(vehicles can ride the ferry) or ✈️ Flight instead."
            )

        # A ferry-free road path existing doesn't mean a real passenger
        # train does — e.g. OSRM can find a fully-land route from India to
        # Saudi Arabia via Pakistan/Iran/Iraq, but there's no interoperable
        # international rail network actually connecting those countries.
        # Without a real rail-network dataset, the safest honest rule is:
        # only offer Train within the same country. This is intentionally
        # conservative — it will also block some real cross-border trains
        # (e.g. Paris–London) rather than risk claiming a route that
        # doesn't exist.
        if origin_country and dest_country and origin_country.strip().lower() != dest_country.strip().lower():
            return False, (
                f"🚆 Train isn't offered for international routes here — {origin_country} and "
                f"{dest_country} may not share a connected passenger rail network, and reliable "
                f"cross-border schedules aren't available from free data sources. "
                f"Try 🚗 Car or ✈️ Flight instead."
            )

    return True, None