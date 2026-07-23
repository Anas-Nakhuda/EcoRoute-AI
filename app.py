"""
🌍 EcoRoute AI — Smart Route & Weather Advisory Agent
Main Streamlit Application

Tech Stack: Streamlit + OSRM + Nominatim + OpenWeather + LangChain + Gemini
"""

import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from config import (
    OPENWEATHER_API_KEY,
    GEMINI_API_KEY,
    TRAVEL_MODES,
    APP_NAME,
    APP_VERSION,
    APP_ICON,
)
from tools.route_tool import fetch_route_complete
from tools.weather_tool import fetch_weather, get_weather_alert_level
from agents.ecoroute_agent import generate_advisory
from components.map_renderer import create_route_map, render_map
from components.ui_components import (
    inject_custom_css,
    render_header,
    render_metrics,
    render_weather_cards,
    render_advisory,
    render_alert_badge,
    render_divider,
    render_section_header,
    render_footer,
    _flatten,
)
from utils.translations import t
from utils.trip_history import save_trip, render_history_sidebar


# ─── Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} — Smart Route & Weather Advisory",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": f"# {APP_NAME} v{APP_VERSION}\nSmart Route & Weather Advisory Agent",
    },
)


# ─── Session State ──────────────────────────────────────────
# Dark theme + English only — no toggles, keeps things simple and reliable.
THEME = "dark"
LANG = "en"

if "results" not in st.session_state:
    st.session_state["results"] = None


def has_valid_keys() -> bool:
    """Check that both API keys are configured in config.py / .env."""
    return bool(OPENWEATHER_API_KEY) and bool(GEMINI_API_KEY)


# ─── Sidebar ────────────────────────────────────────────────
def render_sidebar():
    """Render the sidebar with trip history (no API key inputs, no theme/language
    toggles — those live in config.py / .env, or are fixed to dark + English)."""
    st.sidebar.markdown(f"### {t('sidebar_title', LANG)}")

    # ── Trip History ────────────────────────────
    render_history_sidebar(LANG)

    st.sidebar.markdown("---")

    # ── About ───────────────────────────────────
    st.sidebar.markdown(f"### {t('about_title', LANG)}")
    st.sidebar.caption(t("about_text", LANG))
    st.sidebar.caption(f"v{APP_VERSION}")


# ─── Main App ───────────────────────────────────────────────
def main():
    lang = LANG
    theme = THEME

    # CSS
    inject_custom_css(theme)

    # Sidebar
    render_sidebar()

    # Hero
    render_header(lang)

    # Tagline
    st.markdown(
        f"<p style='text-align: center; opacity: 0.75; margin-top: -0.5rem; "
        f"margin-bottom: 2rem; font-size: 0.95rem;'>"
        f"{t('app_description', lang)}</p>",
        unsafe_allow_html=True,
    )

    # ─── API Key Check ──────────────────────────────────────
    if not has_valid_keys():
        st.markdown(
            _flatten(f"""
            <div class="setup-card">
                <h3>🔑 API Keys Missing</h3>
                <p>This app reads your API keys from <b>config.py</b> (or a <b>.env</b> file
                in the project folder) — not from the app itself.</p>
                <p>
                Open <code>.env</code> and add:<br>
                <code>OPENWEATHER_API_KEY=your_key_here</code><br>
                <code>GEMINI_API_KEY=your_key_here</code>
                </p>
                <p>
                1. <b>OpenWeather</b> → <a href="https://home.openweathermap.org/users/sign_up"
                   target="_blank">Sign up here</a><br>
                2. <b>Google Gemini</b> → <a href="https://aistudio.google.com/"
                   target="_blank">Get key here</a>
                </p>
                <p style="font-size: 0.85rem;">
                💡 After saving the .env file, restart the app (<code>streamlit run app.py</code>).
                </p>
            </div>
            """),
            unsafe_allow_html=True,
        )
        return

    # ─── Input Form ─────────────────────────────────────────
    with st.form("route_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            origin = st.text_input(
                t("origin_label", lang),
                placeholder=t("origin_placeholder", lang),
                key="origin_input",
            )

        with col2:
            destination = st.text_input(
                t("destination_label", lang),
                placeholder=t("destination_placeholder", lang),
                key="dest_input",
            )

        col_mode, col_submit = st.columns([1, 1])

        with col_mode:
            mode_key = st.selectbox(
                t("travel_mode_label", lang),
                options=list(TRAVEL_MODES.keys()),
                key="mode_select",
            )

        with col_submit:
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                t("plan_button", lang),
                use_container_width=True,
            )

    # ─── Process Route ──────────────────────────────────────
    if submitted:
        if not origin:
            st.warning(t("error_no_origin", lang))
            return
        if not destination:
            st.warning(t("error_no_dest", lang))
            return

        owm_key = OPENWEATHER_API_KEY
        gemini_key = GEMINI_API_KEY

        with st.status(t("planning_text", lang), expanded=True) as status:
            # Step 1: Route
            try:
                st.write(t("status_geocoding", lang))
                st.write(t("status_routing", lang))
                route_result = fetch_route_complete(origin, destination)
                origin_geo = route_result["origin_geo"]
                dest_geo = route_result["dest_geo"]
                route_data = route_result["route_data"]
                st.write(f"✅ Route: {route_data['distance_km']} km, {route_data['duration_min']} min")
            except ValueError as e:
                st.error(t("error_geocoding", lang, location=str(e)))
                status.update(label="❌ Failed", state="error")
                return
            except Exception as e:
                st.error(t("error_routing", lang) + f"\n\nDetails: {e}")
                status.update(label="❌ Failed", state="error")
                return

            # Step 2: Weather
            origin_weather = None
            dest_weather = None
            try:
                st.write(t("status_weather", lang))
                origin_weather = fetch_weather(origin_geo["lat"], origin_geo["lon"], owm_key)
                dest_weather = fetch_weather(dest_geo["lat"], dest_geo["lon"], owm_key)
                st.write(f"✅ Origin: {origin_weather['temp_c']}°C, {origin_weather['weather_desc']}")
                st.write(f"✅ Dest: {dest_weather['temp_c']}°C, {dest_weather['weather_desc']}")
            except Exception as e:
                st.warning(t("error_weather", lang) + f" ({e})")
                fallback = {
                    "temp_c": "N/A", "feels_like_c": "N/A", "temp_min_c": "N/A",
                    "temp_max_c": "N/A", "humidity_pct": "N/A", "pressure_hpa": "N/A",
                    "weather_main": "Unknown", "weather_desc": "Unavailable",
                    "weather_icon": "01d", "weather_icon_url": "",
                    "wind_speed_ms": "N/A", "wind_deg": 0, "clouds_pct": "N/A",
                    "visibility_m": "N/A", "location_name": "Unknown",
                }
                origin_weather = origin_weather or fallback
                dest_weather = dest_weather or fallback

            # Step 3: AI Advisory
            advisory_text = ""
            try:
                st.write(t("status_ai", lang))
                origin_name = origin_geo.get("display_name", origin).split(",")[0]
                dest_name = dest_geo.get("display_name", destination).split(",")[0]

                advisory_text = generate_advisory(
                    route_data=route_data,
                    origin_weather=origin_weather,
                    dest_weather=dest_weather,
                    gemini_api_key=gemini_key,
                    language=lang,
                    travel_mode=mode_key,
                    origin_name=origin_name,
                    dest_name=dest_name,
                )
                st.write("✅ AI advisory generated!")
            except Exception as e:
                st.warning(t("error_ai", lang))
                advisory_text = (
                    f"⚠️ **AI Advisory Unavailable**\n\n"
                    f"Could not generate advisory. Error: `{e}`\n\n"
                    f"Please check your Gemini API key in config.py / .env."
                )

            status.update(label=t("status_complete", lang), state="complete")

        # Save to session
        st.session_state.results = {
            "origin_geo": origin_geo,
            "dest_geo": dest_geo,
            "route_data": route_data,
            "origin_weather": origin_weather,
            "dest_weather": dest_weather,
            "advisory": advisory_text,
            "mode_key": mode_key,
            "origin_text": origin,
            "dest_text": destination,
        }

        # Save to history
        try:
            save_trip({
                "origin": origin,
                "destination": destination,
                "mode": TRAVEL_MODES.get(mode_key, {}).get("icon", "🚗"),
                "distance_km": route_data["distance_km"],
                "duration_min": route_data["duration_min"],
                "origin_weather_desc": origin_weather.get("weather_desc", "N/A")
                    if isinstance(origin_weather.get("weather_desc"), str) else "N/A",
                "dest_weather_desc": dest_weather.get("weather_desc", "N/A")
                    if isinstance(dest_weather.get("weather_desc"), str) else "N/A",
                "advisory_summary": advisory_text[:200] if advisory_text else "",
            })
        except Exception:
            pass

    # ─── Display Results ────────────────────────────────────
    if st.session_state.results:
        res = st.session_state.results
        route_data = res["route_data"]
        origin_geo = res["origin_geo"]
        dest_geo = res["dest_geo"]
        origin_weather = res["origin_weather"]
        dest_weather = res["dest_weather"]
        advisory = res["advisory"]
        mode_key = res["mode_key"]

        origin_name = origin_geo.get("display_name", "Origin").split(",")[0]
        dest_name = dest_geo.get("display_name", "Destination").split(",")[0]

        render_divider()

        # ── Route Metrics ───────────────────────────────────
        render_section_header(t("results_title", lang))
        render_metrics(route_data, mode_key, lang)

        # ── Alert Badges ────────────────────────────────────
        if origin_weather and dest_weather:
            st.write("")  # spacing
            c1, c2 = st.columns(2)
            with c1:
                try:
                    render_alert_badge(get_weather_alert_level(origin_weather), lang)
                except Exception:
                    pass
            with c2:
                try:
                    render_alert_badge(get_weather_alert_level(dest_weather), lang)
                except Exception:
                    pass

        render_divider()

        # ── Map ─────────────────────────────────────────────
        render_section_header(t("map_title", lang))
        try:
            route_map = create_route_map(
                route_data=route_data,
                origin_geo=origin_geo,
                dest_geo=dest_geo,
                origin_weather=origin_weather,
                dest_weather=dest_weather,
                theme=theme,
            )
            render_map(route_map, height=500)
        except Exception as e:
            st.error(f"Map error: {e}")

        render_divider()

        # ── Weather ─────────────────────────────────────────
        render_section_header(t("weather_title", lang))
        render_weather_cards(origin_weather, dest_weather, origin_name, dest_name, lang)

        render_divider()

        # ── AI Advisory ─────────────────────────────────────
        render_section_header(t("advisory_title", lang))
        render_advisory(advisory)

        render_divider()

    # Footer
    render_footer()


if __name__ == "__main__":
    main()
