"""
EcoRoute AI — Advisory Agent
Generates a travel advisory (safety tips, eco-driving advice, packing
checklist) using Google Gemini via LangChain.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import GEMINI_MODEL, GEMINI_TEMPERATURE

SYSTEM_PROMPT_EN = (
    "You are EcoRoute AI, a friendly and practical travel advisory assistant. "
    "Given a trip's route, distance, duration, travel mode, and weather at both "
    "ends, write a short, well-organized advisory in Markdown with three "
    "sections using headings: '### 🛡️ Safety Tips', '### 🌱 Eco-Driving Tips', "
    "and '### 🎒 Packing Checklist'. Each section should have 3-5 concise "
    "bullet points. Be specific to the weather conditions and travel mode "
    "given. Keep the whole reply under 220 words. Respond in English."
)

SYSTEM_PROMPT_HI = (
    "आप EcoRoute AI हैं, एक मित्रवत और व्यावहारिक यात्रा सलाहकार सहायक हैं। "
    "यात्रा के मार्ग, दूरी, अवधि, यात्रा के साधन और दोनों छोर के मौसम को "
    "ध्यान में रखते हुए, तीन शीर्षकों के साथ एक संक्षिप्त, सुव्यवस्थित सलाह "
    "मार्कडाउन में लिखें: '### 🛡️ सुरक्षा सुझाव', '### 🌱 इको-ड्राइविंग सुझाव', "
    "और '### 🎒 पैकिंग चेकलिस्ट'। हर भाग में 3-5 संक्षिप्त बुलेट पॉइंट होने "
    "चाहिए। दिए गए मौसम और यात्रा के साधन के अनुसार विशिष्ट रहें। पूरा उत्तर "
    "220 शब्दों से कम रखें। हिंदी में उत्तर दें।"
)


def _build_user_prompt(
    route_data: dict,
    origin_weather: dict,
    dest_weather: dict,
    travel_mode: str,
    origin_name: str,
    dest_name: str,
) -> str:
    return (
        f"Trip: {origin_name} → {dest_name}\n"
        f"Travel mode: {travel_mode}\n"
        f"Distance: {route_data.get('distance_km', 'N/A')} km\n"
        f"Estimated duration: {route_data.get('duration_min', 'N/A')} minutes\n"
        f"Weather at {origin_name}: {origin_weather.get('weather_desc', 'N/A')}, "
        f"{origin_weather.get('temp_c', 'N/A')}°C, wind "
        f"{origin_weather.get('wind_speed_ms', 'N/A')} m/s\n"
        f"Weather at {dest_name}: {dest_weather.get('weather_desc', 'N/A')}, "
        f"{dest_weather.get('temp_c', 'N/A')}°C, wind "
        f"{dest_weather.get('wind_speed_ms', 'N/A')} m/s\n"
    )


def _friendly_error(exc: Exception) -> str:
    """
    Turn Gemini/Google API exceptions (which dump a huge raw JSON blob) into
    a short, actionable message for the UI.
    """
    msg = str(exc)

    if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
        if "limit: 0" in msg or "'limit': 0" in msg:
            return (
                "Your Gemini API key has a **0 free-tier quota** for this model. "
                "This usually means the Google Cloud project behind the key hasn't "
                "been granted free-tier access (common on Workspace/org accounts, "
                "or brand-new projects). Generate a fresh key at "
                "https://aistudio.google.com/apikey using a personal Google account, "
                "or enable billing on the project."
            )
        return (
            "Gemini's free-tier rate limit was hit (too many requests in a short "
            "time, or daily quota used up). Wait a minute and try again, or check "
            "your usage at https://aistudio.google.com/apikey."
        )
    if "API_KEY_INVALID" in msg or "API key not valid" in msg:
        return "This Gemini API key isn't valid. Double-check it at https://aistudio.google.com/apikey."
    if "PERMISSION_DENIED" in msg:
        return "This Gemini API key doesn't have permission to use this model."
    if "NOT_FOUND" in msg and "model" in msg.lower():
        return f"The model '{GEMINI_MODEL}' isn't available for this key/region. Try a different GEMINI_MODEL in config.py."

    # Fall back to a trimmed version of the original message.
    return msg[:300]


def _extract_text(content) -> str:
    """
    Normalize LangChain's response.content into a plain string.

    Newer langchain-google-genai versions can return `content` as a list of
    blocks — e.g. [{'type': 'text', 'text': '...'}] — instead of a plain
    string. The previous version of this function did `str(text)` directly,
    which turned that list into a literal Python-object dump like
    "[{'type': 'text', 'text': 'Hello! ...'}]" and showed up as-is in the
    UI. This extracts and joins just the actual text parts.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") in (None, "text"):
                    parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "\n\n".join(p for p in parts if p)
    return str(content)


def generate_advisory(
    route_data: dict,
    origin_weather: dict,
    dest_weather: dict,
    gemini_api_key: str,
    language: str = "en",
    travel_mode: str = "🚗 Car",
    origin_name: str = "Origin",
    dest_name: str = "Destination",
) -> str:
    """
    Call Gemini (via LangChain) to produce a Markdown travel advisory.
    Raises an exception on failure — the caller (app.py) is responsible
    for catching it and showing a friendly fallback message.
    """
    if not gemini_api_key:
        raise ValueError(
            "Gemini API key is missing. Add GEMINI_API_KEY to your .env file "
            "or config.py."
        )

    system_prompt = SYSTEM_PROMPT_HI if language == "hi" else SYSTEM_PROMPT_EN
    user_prompt = _build_user_prompt(
        route_data, origin_weather, dest_weather, travel_mode, origin_name, dest_name
    )

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=gemini_api_key,
        temperature=GEMINI_TEMPERATURE,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = llm.invoke(messages)
    except Exception as exc:
        raise RuntimeError(_friendly_error(exc)) from exc

    text = _extract_text(getattr(response, "content", None))

    if not text or not text.strip():
        raise RuntimeError("Gemini returned an empty response.")

    return text.strip()