"""
EcoRoute AI — Translations
Simple EN/HI string dictionary + lookup helper.
"""

STRINGS = {
    "sidebar_title": {"en": "⚙️ Settings", "hi": "⚙️ सेटिंग्स"},

    "history_title": {"en": "📜 Trip History", "hi": "📜 यात्रा इतिहास"},
    "history_empty": {"en": "No trips yet. Plan one above!", "hi": "अभी तक कोई यात्रा नहीं। ऊपर एक योजना बनाएं!"},
    "history_clear": {"en": "🗑️ Clear History", "hi": "🗑️ इतिहास साफ़ करें"},

    "about_title": {"en": "ℹ️ About", "hi": "ℹ️ जानकारी"},
    "about_text": {
        "en": "EcoRoute AI plans your route, checks live weather, and gives AI travel advice.",
        "hi": "EcoRoute AI आपका मार्ग बनाता है, मौसम जांचता है, और AI यात्रा सलाह देता है।",
    },

    "app_description": {
        "en": "Plan smarter, greener trips with real-time weather and AI-powered advisories.",
        "hi": "रीयल-टाइम मौसम और AI सलाह के साथ स्मार्ट, हरित यात्राओं की योजना बनाएं।",
    },

    "origin_label": {"en": "📍 From", "hi": "📍 कहाँ से"},
    "origin_placeholder": {"en": "e.g., Ahmedabad", "hi": "जैसे, अहमदाबाद"},
    "destination_label": {"en": "🏁 To", "hi": "🏁 कहाँ तक"},
    "destination_placeholder": {"en": "e.g., Mumbai", "hi": "जैसे, मुंबई"},
    "travel_mode_label": {"en": "🚦 Travel Mode", "hi": "🚦 यात्रा का साधन"},
    "plan_button": {"en": "🚀 Plan Route", "hi": "🚀 मार्ग बनाएं"},

    "error_no_origin": {"en": "Please enter an origin.", "hi": "कृपया प्रारंभिक स्थान दर्ज करें।"},
    "error_no_dest": {"en": "Please enter a destination.", "hi": "कृपया गंतव्य दर्ज करें।"},

    "planning_text": {"en": "Planning your route...", "hi": "आपका मार्ग बनाया जा रहा है..."},
    "status_geocoding": {"en": "📍 Locating places...", "hi": "📍 स्थान खोजे जा रहे हैं..."},
    "status_routing": {"en": "🗺️ Calculating route...", "hi": "🗺️ मार्ग की गणना हो रही है..."},
    "status_weather": {"en": "🌤️ Fetching weather...", "hi": "🌤️ मौसम प्राप्त किया जा रहा है..."},
    "status_ai": {"en": "🤖 Generating AI advisory...", "hi": "🤖 AI सलाह बनाई जा रही है..."},
    "status_complete": {"en": "✅ Done!", "hi": "✅ पूर्ण!"},

    "error_geocoding": {
        "en": "Could not find location: '{location}'. Try a more specific name.",
        "hi": "स्थान नहीं मिला: '{location}'। अधिक स्पष्ट नाम आज़माएं।",
    },
    "error_routing": {"en": "Could not calculate a route between these locations.", "hi": "इन स्थानों के बीच मार्ग नहीं मिल सका।"},
    "error_weather": {"en": "Weather data unavailable.", "hi": "मौसम डेटा उपलब्ध नहीं है।"},
    "error_ai": {"en": "AI advisory could not be generated.", "hi": "AI सलाह नहीं बनाई जा सकी।"},

    "results_title": {"en": "📊 Route Summary", "hi": "📊 मार्ग सारांश"},
    "map_title": {"en": "🗺️ Route Map", "hi": "🗺️ मार्ग मानचित्र"},
    "weather_title": {"en": "🌤️ Weather", "hi": "🌤️ मौसम"},
    "advisory_title": {"en": "🤖 AI Travel Advisory", "hi": "🤖 AI यात्रा सलाह"},

    "metric_distance": {"en": "Distance", "hi": "दूरी"},
    "metric_duration": {"en": "Duration", "hi": "अवधि"},
    "metric_co2": {"en": "CO₂ Estimate", "hi": "CO₂ अनुमान"},

    "w_temp": {"en": "Temperature", "hi": "तापमान"},
    "w_feels_like": {"en": "Feels Like", "hi": "महसूस होता है"},
    "w_humidity": {"en": "Humidity", "hi": "आर्द्रता"},
    "w_wind": {"en": "Wind Speed", "hi": "हवा की गति"},
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Look up a translated string, with optional .format(**kwargs)."""
    entry = STRINGS.get(key)
    if not entry:
        return key
    text = entry.get(lang, entry.get("en", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
