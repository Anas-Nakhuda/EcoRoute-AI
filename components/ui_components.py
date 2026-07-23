"""
EcoRoute AI — UI Components
Custom CSS + reusable Streamlit UI pieces.

Design note: every custom card below sets BOTH its background and its
text color explicitly (with !important) instead of relying on Streamlit's
inherited theme colors. That mismatch — a light-themed card inheriting
Streamlit's default white text, or vice versa — was the cause of the
"disappearing text" bug in the original app.
"""

import streamlit as st

from config import APP_NAME, APP_ICON


def _flatten(html: str) -> str:
    """
    Collapse a multi-line, indented HTML string into a single line.

    Streamlit's Markdown renderer treats 4+ space indented lines as a code
    block, even inside an HTML string with unsafe_allow_html=True. Python's
    triple-quoted f-strings inherit the source file's indentation, so any
    multi-line HTML built that way risks rendering as literal text instead
    of a styled card (this caused the second weather card to show as raw
    HTML). Stripping each line and joining with spaces removes that risk
    while keeping words that wrapped across lines correctly separated
    (HTML collapses repeated whitespace anyway, so extra spaces are safe).
    """
    lines = (line.strip() for line in html.strip().splitlines())
    return " ".join(line for line in lines if line)

# ─── Theme Palettes ─────────────────────────────────────────
THEMES = {
    "dark": {
        "bg": "#0E1117",
        "bg_secondary": "#161B22",
        "card_bg": "rgba(255, 255, 255, 0.06)",
        "card_border": "rgba(255, 255, 255, 0.12)",
        "text_primary": "#F5F7FA",
        "text_secondary": "#B8C0CC",
        "text_muted": "#8792A2",
        "accent": "#00C853",
        "accent_soft": "rgba(0, 200, 83, 0.15)",
    },
    "light": {
        "bg": "#F7F9FC",
        "bg_secondary": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "card_border": "rgba(15, 23, 42, 0.10)",
        "text_primary": "#0F172A",
        "text_secondary": "#3A4759",
        "text_muted": "#64748B",
        "accent": "#00A745",
        "accent_soft": "rgba(0, 167, 69, 0.12)",
    },
}


def inject_custom_css(theme: str = "dark") -> None:
    """Inject global CSS for the chosen theme. Call once near the top of the page."""
    t = THEMES.get(theme, THEMES["dark"])

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {t['bg']};
        }}

        /* Make Streamlit's own text follow the theme, so headers, labels,
           captions, form inputs etc. are always readable. */
        .stApp, .stApp p, .stApp span, .stApp label,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stMarkdown, [data-testid="stMarkdownContainer"] {{
            color: {t['text_primary']};
        }}

        [data-testid="stSidebar"] {{
            background: {t['bg_secondary']};
            border-right: 1px solid {t['card_border']};
        }}
        [data-testid="stSidebar"] * {{
            color: {t['text_primary']} !important;
        }}

        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {{
            background: {t['card_bg']} !important;
            color: {t['text_primary']} !important;
            border: 1px solid {t['card_border']} !important;
        }}
        .stTextInput input::placeholder {{
            color: {t['text_muted']} !important;
            opacity: 1;
        }}

        div[data-testid="stForm"] {{
            background: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 16px;
            padding: 1.5rem;
        }}

        .stButton button, .stFormSubmitButton button {{
            background: {t['accent']} !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }}
        .stButton button:hover, .stFormSubmitButton button:hover {{
            filter: brightness(1.08);
        }}

        /* ── Custom cards ────────────────────────────── */
        .app-header {{
            text-align: center;
            padding: 1.25rem 0 0.25rem 0;
        }}
        .app-header h1 {{
            color: {t['text_primary']} !important;
            font-size: 2.4rem;
            margin-bottom: 0.15rem;
        }}

        .setup-card, .eco-card, .weather-card, .advisory-card {{
            background: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            color: {t['text_primary']} !important;
        }}
        .setup-card *, .eco-card *, .weather-card *, .advisory-card * {{
            color: {t['text_primary']} !important;
        }}
        .setup-card p, .weather-card p {{
            color: {t['text_secondary']} !important;
        }}

        .metric-row {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 0.5rem 0; }}
        .metric-box {{
            flex: 1;
            min-width: 140px;
            background: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 14px;
            padding: 1rem;
            text-align: center;
        }}
        .metric-box .metric-label {{
            color: {t['text_muted']} !important;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .metric-box .metric-value {{
            color: {t['text_primary']} !important;
            font-size: 1.6rem;
            font-weight: 700;
            margin-top: 0.15rem;
        }}

        .weather-grid {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
        .weather-card {{ flex: 1; min-width: 260px; }}
        .weather-card h4 {{ color: {t['text_primary']} !important; margin-bottom: 0.5rem; }}
        .weather-card .w-desc {{ color: {t['accent']} !important; font-weight: 600; }}
        .weather-card .w-row {{
            display: flex; justify-content: space-between;
            padding: 0.3rem 0; border-bottom: 1px dashed {t['card_border']};
            font-size: 0.92rem;
        }}
        .weather-card .w-row span:first-child {{ color: {t['text_muted']} !important; }}
        .weather-card .w-row span:last-child {{ color: {t['text_primary']} !important; font-weight: 600; }}

        .alert-badge {{
            border-radius: 10px;
            padding: 0.6rem 1rem;
            font-weight: 600;
            text-align: center;
        }}
        .alert-good {{ background: rgba(16,185,129,0.15); color: #10B981 !important; border: 1px solid rgba(16,185,129,0.35); }}
        .alert-caution {{ background: rgba(245,158,11,0.15); color: #F59E0B !important; border: 1px solid rgba(245,158,11,0.35); }}
        .alert-warning {{ background: rgba(239,68,68,0.15); color: #EF4444 !important; border: 1px solid rgba(239,68,68,0.35); }}

        .advisory-card {{ line-height: 1.65; }}
        .advisory-card h3 {{ color: {t['accent']} !important; margin-top: 1rem; }}

        .section-header {{
            color: {t['text_primary']} !important;
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0.5rem 0 0.75rem 0;
            border-left: 4px solid {t['accent']};
            padding-left: 0.6rem;
        }}

        .app-footer {{
            text-align: center;
            color: {t['text_muted']} !important;
            font-size: 0.85rem;
            padding: 1.5rem 0 0.5rem 0;
        }}

        hr {{ border-color: {t['card_border']} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(lang: str = "en") -> None:
    from utils.translations import t

    st.markdown(
        _flatten(f"""
        <div class="app-header">
            <h1>{APP_ICON} {APP_NAME}</h1>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_section_header(title: str) -> None:
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def render_divider() -> None:
    st.markdown("<hr/>", unsafe_allow_html=True)


def render_metrics(route_data: dict, mode_key: str, lang: str = "en") -> None:
    from config import TRAVEL_MODES
    from utils.translations import t

    mode_cfg = TRAVEL_MODES.get(mode_key, {})
    distance = route_data.get("distance_km", 0)
    duration = route_data.get("duration_min", 0)
    eco_factor = mode_cfg.get("eco_factor", 0)
    co2_kg = round(distance * eco_factor, 2)

    hours = int(duration // 60)
    minutes = int(duration % 60)
    duration_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"

    st.markdown(
        _flatten(f"""
        <div class="metric-row">
            <div class="metric-box">
                <div class="metric-label">{t('metric_distance', lang)}</div>
                <div class="metric-value">{distance} km</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">{t('metric_duration', lang)}</div>
                <div class="metric-value">{duration_str}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">{t('metric_co2', lang)}</div>
                <div class="metric-value">{co2_kg} kg</div>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_weather_cards(origin_weather: dict, dest_weather: dict, origin_name: str, dest_name: str, lang: str = "en") -> None:
    from utils.translations import t

    def _card(name, w):
        icon_url = w.get("weather_icon_url", "")
        icon_html = f'<img src="{icon_url}" width="48" style="vertical-align:middle;"/>' if icon_url else ""
        return _flatten(f"""
        <div class="weather-card">
            <h4>{icon_html} {name}</h4>
            <div class="w-desc">{w.get('weather_desc', 'N/A')}</div>
            <div class="w-row"><span>{t('w_temp', lang)}</span><span>{w.get('temp_c', 'N/A')}°C</span></div>
            <div class="w-row"><span>{t('w_feels_like', lang)}</span><span>{w.get('feels_like_c', 'N/A')}°C</span></div>
            <div class="w-row"><span>{t('w_humidity', lang)}</span><span>{w.get('humidity_pct', 'N/A')}%</span></div>
            <div class="w-row"><span>{t('w_wind', lang)}</span><span>{w.get('wind_speed_ms', 'N/A')} m/s</span></div>
        </div>
        """)

    st.markdown(
        f'<div class="weather-grid">{_card(origin_name, origin_weather)}{_card(dest_name, dest_weather)}</div>',
        unsafe_allow_html=True,
    )


def render_advisory(advisory_text: str) -> None:
    st.markdown(f'<div class="advisory-card">', unsafe_allow_html=True)
    st.markdown(advisory_text or "_No advisory available._")
    st.markdown("</div>", unsafe_allow_html=True)


def render_alert_badge(alert: dict, lang: str = "en") -> None:
    level = alert.get("level", "good")
    css_class = {"good": "alert-good", "caution": "alert-caution", "warning": "alert-warning"}.get(level, "alert-good")
    st.markdown(
        f'<div class="alert-badge {css_class}">{alert.get("message", "")}</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        _flatten(f"""
        <div class="app-footer">
            {APP_ICON} {APP_NAME} · Built with Streamlit, OSRM, OpenWeather & Gemini
        </div>
        """),
        unsafe_allow_html=True,
    )
