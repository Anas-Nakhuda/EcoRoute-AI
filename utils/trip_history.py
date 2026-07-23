"""
EcoRoute AI — Trip History
Reads/writes trip_history.json and renders the sidebar history list.
"""

import json
import os
from datetime import datetime

import streamlit as st

from config import TRIP_HISTORY_FILE, MAX_HISTORY_ITEMS


def _load_history() -> list:
    if not os.path.exists(TRIP_HISTORY_FILE):
        return []
    try:
        with open(TRIP_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_history(history: list) -> None:
    with open(TRIP_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def save_trip(trip: dict) -> None:
    """Prepend a trip record to trip_history.json, capped at MAX_HISTORY_ITEMS."""
    history = _load_history()
    record = {"timestamp": datetime.now().isoformat(), **trip}
    history.insert(0, record)
    history = history[:MAX_HISTORY_ITEMS]
    _write_history(history)


def clear_history() -> None:
    _write_history([])


def render_history_sidebar(lang: str = "en") -> None:
    from utils.translations import t

    st.sidebar.markdown(f"### {t('history_title', lang)}")
    history = _load_history()

    if not history:
        st.sidebar.caption(t("history_empty", lang))
        return

    for trip in history[:8]:
        origin = trip.get("origin", "?")
        dest = trip.get("destination", "?")
        mode = trip.get("mode", "🚗")
        distance = trip.get("distance_km", "?")
        st.sidebar.markdown(
            f"**{mode} {origin} → {dest}**  \n"
            f"<span style='opacity:0.7; font-size:0.82rem;'>{distance} km</span>",
            unsafe_allow_html=True,
        )

    if st.sidebar.button(t("history_clear", lang), key="clear_history_btn", use_container_width=True):
        clear_history()
        st.rerun()
