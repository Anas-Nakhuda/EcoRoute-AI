# 🌍 EcoRoute AI — Smart Route & Weather Advisory Agent

> **AI-powered travel assistant** that plans routes, fetches real-time weather, and generates intelligent travel advisories using Google Gemini.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-green)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.0_Flash-4285F4?logo=google)

---

## ✨ Features

- 🗺️ **Interactive Route Maps** — Visualize your route with Folium on dark/light themed maps
- 🌤️ **Real-Time Weather** — Live weather data for origin and destination via OpenWeather API
- 🤖 **AI Travel Advisory** — Gemini-powered safety tips, eco-driving advice, and packing checklists
- 🌿 **CO₂ Estimation** — Track your carbon footprint per trip
- 🌐 **Bilingual (EN/HI)** — Full English and Hindi language support
- 📜 **Trip History** — Automatically saves past trips for reference

---

## 🏗️ Architecture

```
EcoRoute AI/
├── app.py                     # Main Streamlit entry point
├── config.py                  # Configuration & constants
├── requirements.txt           # Python dependencies
├── .env.example               # API key template
├── .streamlit/config.toml     # Streamlit theme
├── agents/
│   └── ecoroute_agent.py      # LangChain + Gemini advisory generator
├── tools/
│   ├── route_tool.py          # OSRM + Nominatim routing
│   └── weather_tool.py        # OpenWeather API integration
├── components/
│   ├── map_renderer.py        # Folium map visualization
│   └── ui_components.py       # Premium UI components & CSS
└── utils/
    ├── translations.py        # EN/HI translations
    └── trip_history.py        # Trip history persistence
```

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  User Input: "Ahmedabad → Mumbai by Car"                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   1. Nominatim Geocode  │  (Free, No Key)
          │   → Get Coordinates     │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   2. OSRM Routing       │  (Free, No Key)
          │   → Distance, Duration  │
          │   → Route Geometry      │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   3. OpenWeather API    │  (Free Key)
          │   → Origin Weather      │
          │   → Destination Weather │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   4. Gemini AI (LLM)    │  (Free Key)
          │   → Safety Advisory     │
          │   → Eco-Driving Tips    │
          │   → Packing Checklist   │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   5. Streamlit UI       │
          │   → Interactive Map     │
          │   → Weather Cards       │
          │   → AI Advisory Panel   │
          └─────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
# Navigate to project directory
cd "EcoRoute AI"

# Install dependencies
pip install -r requirements.txt
```

### 2. Get API Keys (Only 2 needed — both free!)

| Service | Purpose | Get Key |
|---------|---------|---------|
| **OpenWeather** | Live weather data | [openweathermap.org](https://home.openweathermap.org/users/sign_up) |
| **Google Gemini** | AI advisory | [aistudio.google.com](https://aistudio.google.com/) |

> **Note**: OSRM and Nominatim are **completely free** with no API key required!

### 3. Configure Keys

Keys are read from a `.env` file only — there is **no key input in the app UI**.

```bash
# A .env file is already included in this folder — just open it and paste your keys:
OPENWEATHER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

(If it's missing, copy `.env.example` to `.env` first.)

### 4. Run

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` 🎉

---


## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.9+** | Core language |
| **Streamlit** | Web framework |
| **LangChain** | AI orchestration |
| **Google Gemini 2.0 Flash** | LLM for advisories |
| **OSRM** | Route calculation |
| **Nominatim** | Geocoding |
| **OpenWeather API** | Weather data |
| **Folium** | Interactive maps |

---

## 🌟 Future Enhancements

- [ ] Multi-stop route planning
- [ ] Voice input support
- [ ] Traffic data integration
- [ ] Email trip summary
- [ ] Mobile-responsive PWA
- [ ] Route comparison (multiple routes)
- [ ] Integration with Google Maps links

---



## 🙏 Acknowledgements

- [OSRM](https://project-osrm.org/) — Open Source Routing Machine
- [OpenStreetMap](https://www.openstreetmap.org/) — Map data via Nominatim
- [OpenWeather](https://openweathermap.org/) — Weather API
- [Google Gemini](https://ai.google.dev/) — AI/LLM
- [Streamlit](https://streamlit.io/) — Web framework
- [Folium](https://python-visualization.github.io/folium/) — Map visualization


## Author
* Anas Nakhuda
