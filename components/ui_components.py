"""
EcoRoute AI — UI Components
Custom CSS + reusable Streamlit UI pieces.

Design note: every custom card below sets BOTH its background and its
text color explicitly (with !important) instead of relying on Streamlit's
inherited theme colors. That mismatch — a light-themed card inheriting
Streamlit's default white text, or vice versa — was the cause of the
"disappearing text" bug in the original app.
"""

import ast

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


def normalize_advisory_text(raw) -> str:
    """
    Coerce whatever the AI agent returned into clean Markdown text.

    The Gemini/LangChain response can come back in a few different shapes
    depending on the model + library version:
      - a plain string of Markdown (the happy path),
      - a list of content blocks, e.g. [{'type': 'text', 'text': '...'}],
      - a dict with a 'text' key,
      - or — if something upstream already called str() on one of the
        above — a *string* that literally looks like "[{'type': 'text', ...}]".

    Without this normalization, that last case renders as a raw Python
    object dump in the UI (exactly what showed up in the AI Advisory
    panel). This function detects and unwraps all of these cases so the
    user always sees clean formatted text.
    """
    if raw is None:
        return ""

    value = raw

    # A string that *looks* like a Python list/dict literal — try to parse it.
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                value = ast.literal_eval(stripped)
            except (ValueError, SyntaxError):
                return value  # genuinely plain text, leave as-is
        else:
            return value

    if isinstance(value, dict):
        value = [value]

    if isinstance(value, list):
        parts = []
        for block in value:
            if isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "\n\n".join(p for p in parts if p).strip()

    return str(value)


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
            background:
                radial-gradient(circle at 12% 8%, {t['accent_soft']} 0%, transparent 32%),
                {t['bg']};
        }}

        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes breathe {{
            0%, 100% {{ box-shadow: 0 0 0 5px {t['accent_soft']}; }}
            50% {{ box-shadow: 0 0 0 9px {t['accent_soft']}; }}
        }}
        @keyframes popIn {{
            0% {{ transform: scale(0.6); opacity: 0; }}
            60% {{ transform: scale(1.12); opacity: 1; }}
            100% {{ transform: scale(1); opacity: 1; }}
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
            border-radius: 10px !important;
        }}
        .stTextInput input::placeholder {{
            color: {t['text_muted']} !important;
            opacity: 1;
        }}
        .stTextInput input:focus {{
            border-color: {t['accent']} !important;
            box-shadow: 0 0 0 3px {t['accent_soft']} !important;
        }}

        div[data-testid="stForm"] {{
            background: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 18px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        }}

        .stButton button, .stFormSubmitButton button {{
            background: linear-gradient(135deg, {t['accent']}, #00E676) !important;
            color: #06210F !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }}
        .stButton button:hover, .stFormSubmitButton button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 16px {t['accent_soft']};
        }}

        /* ── Header ──────────────────────────────────── */
        .app-header {{
            text-align: center;
            padding: 1.25rem 0 0.25rem 0;
        }}
        .app-header h1 {{
            background: linear-gradient(135deg, {t['text_primary']} 30%, {t['accent']} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.6rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
            letter-spacing: -0.02em;
        }}

        /* ── Custom cards ────────────────────────────── */
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

        /* ── Metrics ─────────────────────────────────── */
        .metric-row {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 0.5rem 0; }}
        .metric-box {{
            position: relative;
            overflow: hidden;
            flex: 1;
            min-width: 150px;
            background: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 14px;
            padding: 1.1rem 1rem 0.9rem 1rem;
            text-align: center;
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            animation: fadeInUp 0.45s ease both;
        }}
        .metric-row .metric-box:nth-child(1) {{ animation-delay: 0.05s; }}
        .metric-row .metric-box:nth-child(2) {{ animation-delay: 0.15s; }}
        .metric-row .metric-box:nth-child(3) {{ animation-delay: 0.25s; }}
        .metric-box::before {{
            content: "";
            position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, {t['accent']}, transparent);
        }}
        .metric-box:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 24px rgba(0,0,0,0.22);
        }}
        .metric-box .metric-icon {{ font-size: 1.25rem; margin-bottom: 0.2rem; }}
        .metric-box .metric-label {{
            color: {t['text_muted']} !important;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .metric-box .metric-value {{
            color: {t['text_primary']} !important;
            font-size: 1.65rem;
            font-weight: 700;
            margin-top: 0.15rem;
        }}

        /* ── Weather cards ───────────────────────────── */
        .weather-grid {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
        .weather-card {{
            flex: 1; min-width: 260px;
            transition: transform 0.18s ease;
            animation: fadeInUp 0.5s ease both;
        }}
        .weather-card:hover {{ transform: translateY(-2px); }}
        .weather-grid .weather-card:nth-child(2) {{ animation-delay: 0.12s; }}
        .weather-card h4 {{ color: {t['text_primary']} !important; margin-bottom: 0.5rem; }}
        .weather-card .w-desc {{ color: {t['accent']} !important; font-weight: 600; }}
        .weather-card .w-row {{
            display: flex; justify-content: space-between;
            padding: 0.3rem 0; border-bottom: 1px dashed {t['card_border']};
            font-size: 0.92rem;
        }}
        .weather-card .w-row span:first-child {{ color: {t['text_muted']} !important; }}
        .weather-card .w-row span:last-child {{ color: {t['text_primary']} !important; font-weight: 600; }}

        /* ── Per-city condition badges ───────────────── */
        .alert-badge {{
            border-radius: 14px;
            padding: 0.75rem 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
            animation: fadeInUp 0.45s ease both;
        }}
        .alert-badge-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 700;
        }}
        .alert-badge-top span:last-child {{ display: inline-block; animation: popIn 0.4s ease 0.2s both; }}
        .alert-location {{ display: flex; align-items: center; gap: 0.35rem; }}
        .alert-message {{ font-size: 0.88rem; opacity: 0.92; }}
        .alert-good {{ background: rgba(16,185,129,0.15); color: #10B981 !important; border: 1px solid rgba(16,185,129,0.35); }}
        .alert-caution {{ background: rgba(245,158,11,0.15); color: #F59E0B !important; border: 1px solid rgba(245,158,11,0.35); }}
        .alert-warning {{ background: rgba(239,68,68,0.15); color: #EF4444 !important; border: 1px solid rgba(239,68,68,0.35); }}

        /* ── AI Advisory ─────────────────────────────── */
        .advisory-header {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.75rem;
        }}
        .advisory-badge {{
            background: linear-gradient(135deg, {t['accent']}, #00E676);
            color: #06210F !important;
            font-weight: 800;
            font-size: 0.72rem;
            letter-spacing: 0.04em;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            animation: popIn 0.4s ease both;
        }}
        .advisory-title-text {{
            font-weight: 700;
            color: {t['text_primary']} !important;
            animation: fadeInUp 0.4s ease 0.05s both;
        }}
        .advisory-card {{
            line-height: 1.7;
            border-left: 3px solid {t['accent']};
            animation: fadeInUp 0.5s ease 0.1s both;
        }}
        .advisory-card h3 {{ color: {t['accent']} !important; margin-top: 1rem; }}

        /* ── Animated progress tracker ───────────────── */
        .progress-tracker {{
            display: flex;
            align-items: flex-start;
            background: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 16px;
            padding: 1.4rem 1.25rem 1.1rem 1.25rem;
            margin: 0.5rem 0 1rem 0;
            overflow-x: auto;
        }}
        .step-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            flex: 1;
            min-width: 100px;
        }}
        .step-icon-wrap {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.15rem;
            background: {t['bg_secondary']};
            border: 2px solid {t['card_border']};
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
        }}
        .step-pending .step-icon-wrap {{ opacity: 0.4; }}
        .step-active .step-icon-wrap {{
            border-color: {t['accent']};
            animation: breathe 1.6s ease-in-out infinite;
        }}
        .step-done .step-icon-wrap {{
            border-color: {t['accent']};
            background: {t['accent_soft']};
            animation: popIn 0.35s ease both;
        }}
        .step-error .step-icon-wrap {{
            border-color: #EF4444;
            background: rgba(239,68,68,0.14);
            animation: popIn 0.35s ease both;
        }}
        .step-label {{
            font-size: 0.8rem;
            font-weight: 600;
            color: {t['text_secondary']} !important;
            transition: color 0.3s ease;
        }}
        .step-active .step-label, .step-done .step-label {{ color: {t['text_primary']} !important; }}
        .step-detail {{
            font-size: 0.72rem;
            color: {t['accent']} !important;
            margin-top: 0.2rem;
            font-weight: 600;
            animation: fadeInUp 0.35s ease both;
        }}
        .step-connector {{
            flex: 0.5;
            height: 2px;
            background: {t['card_border']};
            margin-top: 21px;
            min-width: 24px;
            transition: background 0.5s ease;
        }}
        .step-connector.filled {{ background: {t['accent']}; }}
        .step-spinner {{
            width: 16px;
            height: 16px;
            border: 2px solid {t['accent_soft']};
            border-top-color: {t['accent']};
            border-radius: 50%;
            animation: eco-spin 0.8s linear infinite;
        }}
        @keyframes eco-spin {{ to {{ transform: rotate(360deg); }} }}

        /* ── Trip history (sidebar) ──────────────────── */
        @keyframes slideInLeft {{
            from {{ opacity: 0; transform: translateX(-8px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}
        .history-card {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            background: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 12px;
            padding: 0.55rem 0.7rem;
            margin-bottom: 0.5rem;
            transition: border-color 0.18s ease, transform 0.15s ease;
            animation: slideInLeft 0.35s ease both;
        }}
        .history-card:nth-child(1) {{ animation-delay: 0.02s; }}
        .history-card:nth-child(2) {{ animation-delay: 0.06s; }}
        .history-card:nth-child(3) {{ animation-delay: 0.10s; }}
        .history-card:nth-child(4) {{ animation-delay: 0.14s; }}
        .history-card:nth-child(5) {{ animation-delay: 0.18s; }}
        .history-card:hover {{
            border-color: {t['accent']};
            transform: translateX(2px);
        }}
        .history-icon {{
            width: 32px; height: 32px; border-radius: 50%;
            background: {t['accent_soft']};
            display: flex; align-items: center; justify-content: center;
            font-size: 0.95rem; flex-shrink: 0;
        }}
        .history-info {{ display: flex; flex-direction: column; line-height: 1.25; overflow: hidden; }}
        .history-route {{
            font-size: 0.84rem; font-weight: 700; color: {t['text_primary']} !important;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }}
        .history-meta {{ font-size: 0.71rem; color: {t['text_muted']} !important; }}

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
                <div class="metric-icon">📏</div>
                <div class="metric-label">{t('metric_distance', lang)}</div>
                <div class="metric-value">{distance} km</div>
            </div>
            <div class="metric-box">
                <div class="metric-icon">⏱️</div>
                <div class="metric-label">{t('metric_duration', lang)}</div>
                <div class="metric-value">{duration_str}</div>
            </div>
            <div class="metric-box">
                <div class="metric-icon">🌱</div>
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


def render_mode_notice(message: str, tone: str = "caution") -> None:
    """
    Full-width banner used to flag when the chosen travel mode isn't
    realistic for the given distance (e.g. cycling 300 km, or taking a
    train for a 5 km hop). Reuses the same color language as the weather
    condition badges so it reads as "pay attention to this" without
    looking like an error.
    """
    css_class = {"good": "alert-good", "caution": "alert-caution", "warning": "alert-warning"}.get(tone, "alert-caution")
    st.markdown(
        _flatten(f"""
        <div class="alert-badge {css_class}" style="margin: 0.5rem 0 1rem 0;">
            <div class="alert-message" style="font-size:0.95rem; font-weight:600;">{message}</div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_advisory(advisory_text) -> None:
    clean_text = normalize_advisory_text(advisory_text)
    st.markdown(
        _flatten("""
        <div class="advisory-header">
            <span class="advisory-badge">AI</span>
            <span class="advisory-title-text">Your Travel Advisory</span>
        </div>
        """),
        unsafe_allow_html=True,
    )
    st.markdown('<div class="advisory-card">', unsafe_allow_html=True)
    st.markdown(clean_text or "_No advisory available._")
    st.markdown("</div>", unsafe_allow_html=True)


def render_alert_badge(alert: dict, lang: str = "en", location_name: str = "", icon_url: str = "") -> None:
    level = alert.get("level", "good")
    css_class = {"good": "alert-good", "caution": "alert-caution", "warning": "alert-warning"}.get(level, "alert-good")
    emoji = {"good": "✅", "caution": "⚠️", "warning": "🚨"}.get(level, "✅")
    icon_html = f'<img src="{icon_url}" width="24" style="vertical-align:middle; margin-right:2px;"/>' if icon_url else ""

    st.markdown(
        _flatten(f"""
        <div class="alert-badge {css_class}">
            <div class="alert-badge-top">
                <span class="alert-location">{icon_html} {location_name or ''}</span>
                <span>{emoji}</span>
            </div>
            <div class="alert-message">{alert.get('message', '')}</div>
        </div>
        """),
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


# ─── Animated Progress Tracker ───────────────────────────────
class ProgressTracker:
    """
    Renders a horizontal, animated step tracker (instead of the plain
    st.status text log) and lets the caller update step states/details
    as the pipeline (geocode -> route -> weather -> AI) progresses.

    Usage:
        tracker = render_progress_tracker()
        steps = [
            {"icon": "📍", "label": "Locating places", "state": "active"},
            {"icon": "🗺️", "label": "Calculating route", "state": "pending"},
        ]
        tracker.update(steps)
        ...
        steps[0]["state"] = "done"
        steps[1]["state"] = "active"
        tracker.update(steps)
    """

    def __init__(self, placeholder):
        self._placeholder = placeholder

    def update(self, steps: list) -> None:
        n = len(steps)
        items_html = []

        for i, step in enumerate(steps):
            state = step.get("state", "pending")
            icon = step.get("icon", "•")
            label = step.get("label", "")
            detail = step.get("detail", "")

            if state == "done":
                icon_html = "✅"
            elif state == "active":
                icon_html = '<span class="step-spinner"></span>'
            elif state == "error":
                icon_html = "❌"
            else:
                icon_html = icon

            detail_html = f'<div class="step-detail">{detail}</div>' if detail else ""

            items_html.append(_flatten(f"""
                <div class="step-item step-{state}">
                    <div class="step-icon-wrap">{icon_html}</div>
                    <div class="step-label">{label}</div>
                    {detail_html}
                </div>
            """))

            if i < n - 1:
                filled = "filled" if step.get("state") == "done" else ""
                items_html.append(f'<div class="step-connector {filled}"></div>')

        html = f'<div class="progress-tracker">{"".join(items_html)}</div>'
        self._placeholder.markdown(html, unsafe_allow_html=True)


def render_progress_tracker() -> ProgressTracker:
    """Reserve a spot in the layout and return a ProgressTracker bound to it."""
    placeholder = st.empty()
    return ProgressTracker(placeholder)