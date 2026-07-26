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
# `kind` classifies how a mode's distance/feasibility is computed:
#   "road"   — uses OSRM road distance; ferries are fine (Car/Bike/Walk
#              can all ride a ferry as vehicle/foot/bike passengers)
#   "rail"   — uses OSRM road distance as a rail-distance approximation,
#              but is blocked if the route requires a sea ferry crossing
#              (no direct train service crosses open water)
#   "flight" — uses great-circle distance instead of road distance, since
#              flights don't follow roads at all
#
# `avg_speed_kmh` drives the *displayed* duration — see app.py, where it
# overrides OSRM's raw duration. This matters because OSRM's free demo
# server only supports the "driving" profile, so without this override
# every mode (even Walk) would show car-speed timing for the same route.
#
# `max_realistic_km` / `min_realistic_km` are soft guardrails: if a chosen
# mode is unrealistic for the given distance (e.g. cycling 300 km), the
# app shows a friendly notice suggesting a better-suited mode instead of
# silently presenting a misleading duration. This is separate from hard
# feasibility (see check_mode_feasibility in tools/route_tool.py), which
# blocks modes that are physically impossible for the route rather than
# just impractical.
TRAVEL_MODES = {
    "🚗 Car": {
        "osrm_profile": "driving",
        "icon": "🚗",
        "kind": "road",
        "avg_speed_kmh": 60,
        "eco_factor": 0.21,  # kg CO2 per km
        "max_realistic_km": None,
        "min_realistic_km": None,
    },
    "🚆 Train": {
        # No public rail-routing API is wired up here, so road distance
        # from OSRM is used as an approximation of rail distance — it's
        # usually in the right ballpark for intercity routes, but real
        # rail corridors can differ from road corridors. Blocked entirely
        # when the route requires a sea ferry crossing (see route_tool.py).
        "osrm_profile": "driving",
        "icon": "🚆",
        "kind": "rail",
        "avg_speed_kmh": 55,  # realistic express-train average incl. stops
        "eco_factor": 0.045,  # kg CO2 per km per passenger — rail is far cleaner than road
        "max_realistic_km": None,
        "min_realistic_km": 60,  # not worth suggesting a train for very short hops
    },
    "✈️ Flight": {
        "osrm_profile": None,  # not routed via OSRM — great-circle distance is used instead
        "icon": "✈️",
        "kind": "flight",
        "avg_speed_kmh": 700,  # typical commercial jet cruise speed
        "fixed_overhead_min": 90,  # check-in, security, taxi, boarding, climb/descent
        "eco_factor": 0.15,  # kg CO2 per km per passenger (aviation average)
        "max_realistic_km": None,
        "min_realistic_km": 150,  # flying isn't practical for very short hops
    },
    "🚲 Bike": {
        "osrm_profile": "driving",  # OSRM demo server only supports driving
        "icon": "🚲",
        "kind": "road",
        "avg_speed_kmh": 15,
        "eco_factor": 0.0,
        "max_realistic_km": 80,  # beyond this, a single-day cycling trip is unrealistic
        "min_realistic_km": None,
    },
    "🚶 Walk": {
        "osrm_profile": "driving",  # OSRM demo server only supports driving
        "icon": "🚶",
        "kind": "road",
        "avg_speed_kmh": 5,
        "eco_factor": 0.0,
        "max_realistic_km": 20,  # beyond this, walking stops being a realistic single trip
        "min_realistic_km": None,
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
GEMINI_MODEL = "gemini-flash-latest"
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
