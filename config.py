"""
EcoRoute AI — Configuration
Central configuration for API endpoints, travel modes, and app constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ───────────────────────────────────────────────
# Paste your keys directly here, OR (recommended) put them in a
# ".env" file in this same folder as:
#   OPENWEATHER_API_KEY=your_key_here
#   GEMINI_API_KEY=your_key_here
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ─── API Endpoints (OSRM & Nominatim — No Keys Needed) ─────
OSRM_BASE_URL = "https://router.project-osrm.org/route/v1"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"

# ─── OpenWeather ────────────────────────────────────────────
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
WEATHER_ICON_URL = "https://openweathermap.org/img/wn/{icon}@2x.png"

# ─── Travel Modes ──────────────────────────────────────────
TRAVEL_MODES = {
    "🚗 Car": {
        "osrm_profile": "driving",
        "icon": "🚗",
        "avg_speed_kmh": 60,
        "eco_factor": 0.21,  # kg CO2 per km
    },
    "🚲 Bike": {
        "osrm_profile": "driving",  # OSRM demo server only supports driving
        "icon": "🚲",
        "avg_speed_kmh": 15,
        "eco_factor": 0.0,
    },
    "🚶 Walk": {
        "osrm_profile": "driving",  # OSRM demo server only supports driving
        "icon": "🚶",
        "avg_speed_kmh": 5,
        "eco_factor": 0.0,
    },
}

# ─── App Constants ──────────────────────────────────────────
APP_NAME = "EcoRoute AI"
APP_TAGLINE_EN = "Smart Route & Weather Advisory Agent"
APP_TAGLINE_HI = "स्मार्ट रूट और मौसम सलाहकार एजेंट"
APP_VERSION = "1.0.0"
APP_ICON = "🌍"
TRIP_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "trip_history.json")
MAX_HISTORY_ITEMS = 50

# ─── Gemini Model ───────────────────────────────────────────
# "gemini-2.0-flash" is fast + free-tier friendly. If you hit quota
# errors (HTTP 429), you can switch this to "gemini-1.5-flash".
GEMINI_MODEL = "models/gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.7

# ─── Map Themes ─────────────────────────────────────────────
MAP_TILES = {
    "dark": {
        "tiles": "CartoDB dark_matter",
        "name": "Dark",
    },
    "light": {
        "tiles": "CartoDB positron",
        "name": "Light",
    },
}

ROUTE_COLOR = "#00C853"
ROUTE_WEIGHT = 5
ROUTE_OPACITY = 0.85
