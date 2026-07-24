"""
EcoRoute AI — Map Renderer
Builds and renders the Folium route map.
"""

import folium
from streamlit_folium import st_folium

from config import MAP_TILES, ROUTE_COLOR, ROUTE_WEIGHT, ROUTE_OPACITY


def create_route_map(
    route_data: dict,
    origin_geo: dict,
    dest_geo: dict,
    origin_weather: dict,
    dest_weather: dict,
    theme: str = "dark",
) -> folium.Map:
    """Build a Folium map with the route line and origin/destination markers."""
    geometry = route_data.get("geometry", [])

    # Center the map on the midpoint of the route (or origin if geometry is empty).
    if geometry:
        mid = geometry[len(geometry) // 2]
    else:
        mid = [origin_geo["lat"], origin_geo["lon"]]

    tile_cfg = MAP_TILES.get(theme, MAP_TILES["dark"])

    fmap = folium.Map(
        location=mid,
        zoom_start=7,
        tiles=tile_cfg["tiles"],
        control_scale=True,
    )

    if geometry:
        folium.PolyLine(
            geometry,
            color=ROUTE_COLOR,
            weight=ROUTE_WEIGHT,
            opacity=ROUTE_OPACITY,
        ).add_to(fmap)
        fmap.fit_bounds(geometry)

    origin_short = origin_geo.get("display_name", "Origin").split(",")[0]
    dest_short = dest_geo.get("display_name", "Destination").split(",")[0]

    # Origin marker — tooltip now shows weather at a glance, on hover,
    # so the user doesn't have to click the pin to know what's going on there.
    origin_desc = origin_weather.get("weather_desc", "N/A")
    origin_temp = origin_weather.get("temp_c", "N/A")
    origin_popup = (
        f"<b>Origin:</b> {origin_short}<br>"
        f"{origin_desc}, {origin_temp}°C"
    )
    folium.Marker(
        location=[origin_geo["lat"], origin_geo["lon"]],
        popup=folium.Popup(origin_popup, max_width=250),
        tooltip=f"🟢 {origin_short} — {origin_desc}, {origin_temp}°C",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(fmap)

    # Destination marker
    dest_desc = dest_weather.get("weather_desc", "N/A")
    dest_temp = dest_weather.get("temp_c", "N/A")
    dest_popup = (
        f"<b>Destination:</b> {dest_short}<br>"
        f"{dest_desc}, {dest_temp}°C"
    )
    folium.Marker(
        location=[dest_geo["lat"], dest_geo["lon"]],
        popup=folium.Popup(dest_popup, max_width=250),
        tooltip=f"🔴 {dest_short} — {dest_desc}, {dest_temp}°C",
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
    ).add_to(fmap)

    return fmap


def render_map(fmap: folium.Map, height: int = 500) -> None:
    """Render a Folium map inside Streamlit."""
    st_folium(fmap, height=height, use_container_width=True, returned_objects=[])