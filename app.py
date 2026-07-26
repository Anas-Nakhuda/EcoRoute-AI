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
from tools.route_tool import fetch_route_complete, check_mode_feasibility
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
    render_progress_tracker,
    normalize_advisory_text,
    render_mode_notice,
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

        # ── Animated progress tracker (replaces the plain st.status log) ──
        steps = [
            {"icon": "📍", "label": t("status_geocoding", lang), "state": "active"},
            {"icon": "🗺️", "label": t("status_routing", lang), "state": "pending"},
            {"icon": "🌤️", "label": t("status_weather", lang), "state": "pending"},
            {"icon": "🤖", "label": t("status_ai", lang), "state": "pending"},
        ]
        tracker = render_progress_tracker()
        tracker.update(steps)

        # Step 1 + 2: Geocoding + Route (fetch_route_complete does both)
        try:
            route_result = fetch_route_complete(origin, destination)
            origin_geo = route_result["origin_geo"]
            dest_geo = route_result["dest_geo"]
            route_data = route_result["route_data"]  # None if no road/ferry path exists at all
            great_circle_km = route_result["great_circle_km"]

            mode_cfg = TRAVEL_MODES.get(mode_key, {})

            # Hard feasibility check FIRST — is this mode even physically
            # possible for this route? (e.g. no train can cross open ocean,
            # no ground mode works if there's no road/ferry path at all.)
            feasible, infeasible_reason = check_mode_feasibility(
                mode_cfg,
                route_data,
                great_circle_km,
                origin_country=origin_geo.get("country", ""),
                dest_country=dest_geo.get("country", ""),
            )
            if not feasible:
                steps[0]["state"] = "done"
                steps[1]["state"] = "error"
                steps[1]["detail"] = "Not possible for this mode"
                tracker.update(steps)
                st.error(f"🚫 {infeasible_reason}")
                return

            if mode_cfg.get("kind") == "flight":
                # Flights don't follow roads — use great-circle distance with
                # a small routing-inefficiency margin, realistic cruise speed,
                # plus fixed overhead for check-in/security/taxi/boarding.
                distance_km = round(great_circle_km * 1.05, 2)
                cruise_speed = mode_cfg.get("avg_speed_kmh", 700)
                overhead_min = mode_cfg.get("fixed_overhead_min", 90)
                duration_min = round((distance_km / cruise_speed) * 60 + overhead_min, 1)
                route_data = {
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "geometry": [],  # no road geometry for flights
                    "ferry_km": 0.0,
                    "has_ferry": False,
                }
            else:
                # OSRM's free demo server only routes with the "driving"
                # profile, so its raw duration reflects car speeds no matter
                # which mode is selected. Recalculate using the chosen
                # mode's realistic average speed, keeping OSRM's road
                # distance as the base figure.
                avg_speed = mode_cfg.get("avg_speed_kmh")
                if avg_speed:
                    route_data["duration_min"] = round(
                        (route_data["distance_km"] / avg_speed) * 60, 1
                    )

            # Soft realism guardrails — the mode IS physically possible,
            # just impractical at this distance (or involves a ferry leg
            # worth calling out even though it doesn't block the mode).
            mode_warning = None
            if route_data.get("has_ferry") and mode_cfg.get("kind") != "flight":
                mode_warning = f"⛴️ This route includes a ~{route_data['ferry_km']} km ferry crossing."

            max_km = mode_cfg.get("max_realistic_km")
            min_km = mode_cfg.get("min_realistic_km")
            distance_km = route_data["distance_km"]
            realism_note = None
            if max_km and distance_km > max_km:
                realism_note = (
                    f"⚠️ {distance_km} km is a long way to cover by {mode_key.split(' ', 1)[-1].lower()} "
                    f"in one trip. The duration below assumes a steady pace the whole way — "
                    f"for a route this long, Car, Train, or Flight would be more realistic."
                )
            elif min_km and distance_km < min_km:
                realism_note = (
                    f"ℹ️ {mode_key.split(' ', 1)[-1]} usually isn't the fastest choice for a "
                    f"{distance_km} km hop — Car or Bike will likely get you there quicker door-to-door."
                )
            if realism_note:
                mode_warning = f"{mode_warning} {realism_note}" if mode_warning else realism_note

            steps[0]["state"] = "done"
            steps[1]["state"] = "done"
            steps[1]["detail"] = f"{route_data['distance_km']} km · {route_data['duration_min']} min"
            steps[2]["state"] = "active"
            tracker.update(steps)
        except ValueError as e:
            steps[0]["state"] = "error"
            tracker.update(steps)
            st.error(t("error_geocoding", lang, location=str(e)))
            return
        except Exception as e:
            steps[0]["state"] = "done"
            steps[1]["state"] = "error"
            tracker.update(steps)
            st.error(t("error_routing", lang) + f"\n\nDetails: {e}")
            return

        # Step 3: Weather
        origin_weather = None
        dest_weather = None
        try:
            origin_weather = fetch_weather(origin_geo["lat"], origin_geo["lon"], owm_key)
            dest_weather = fetch_weather(dest_geo["lat"], dest_geo["lon"], owm_key)

            steps[2]["state"] = "done"
            steps[2]["detail"] = f"{origin_weather['temp_c']}°C / {dest_weather['temp_c']}°C"
            steps[3]["state"] = "active"
            tracker.update(steps)
        except Exception as e:
            steps[2]["state"] = "error"
            tracker.update(steps)
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
            steps[3]["state"] = "active"
            tracker.update(steps)

        # Step 4: AI Advisory
        advisory_text = ""
        try:
            origin_name = origin_geo.get("display_name", origin).split(",")[0]
            dest_name = dest_geo.get("display_name", destination).split(",")[0]

            raw_advisory = generate_advisory(
                route_data=route_data,
                origin_weather=origin_weather,
                dest_weather=dest_weather,
                gemini_api_key=gemini_key,
                language=lang,
                travel_mode=mode_key,
                origin_name=origin_name,
                dest_name=dest_name,
            )
            # Normalize here regardless of what shape the agent returned
            # (plain string, list of content blocks, etc.) — this is the
            # fix for the AI Advisory panel showing raw Python object text.
            advisory_text = normalize_advisory_text(raw_advisory)

            steps[3]["state"] = "done"
            tracker.update(steps)
        except Exception as e:
            steps[3]["state"] = "error"
            tracker.update(steps)
            st.warning(t("error_ai", lang))
            advisory_text = (
                f"⚠️ **AI Advisory Unavailable**\n\n"
                f"Could not generate advisory. Error: `{e}`\n\n"
                f"Please check your Gemini API key in config.py / .env."
            )

        # Save to session
        st.session_state.results = {
            "origin_geo": origin_geo,
            "dest_geo": dest_geo,
            "route_data": route_data,
            "origin_weather": origin_weather,
            "dest_weather": dest_weather,
            "advisory": advisory_text,
            "mode_key": mode_key,
            "mode_warning": mode_warning,
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
                "advisory_summary": normalize_advisory_text(advisory_text)[:200] if advisory_text else "",
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
        if res.get("mode_warning"):
            render_mode_notice(res["mode_warning"])
        render_metrics(route_data, mode_key, lang)

        # ── Alert Badges (now labeled per city, so it's clear which
        #    weather condition belongs to origin vs destination) ──
        if origin_weather and dest_weather:
            st.write("")  # spacing
            c1, c2 = st.columns(2)
            with c1:
                try:
                    render_alert_badge(
                        get_weather_alert_level(origin_weather),
                        lang,
                        location_name=origin_name,
                        icon_url=origin_weather.get("weather_icon_url", ""),
                    )
                except Exception:
                    pass
            with c2:
                try:
                    render_alert_badge(
                        get_weather_alert_level(dest_weather),
                        lang,
                        location_name=dest_name,
                        icon_url=dest_weather.get("weather_icon_url", ""),
                    )
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