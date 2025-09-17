# BearFruit
# Copyright (c) 2025 Arya Reiland

# ----------------------------- Imports (top-only) -----------------------------
import io
import time
import json
import mimetypes
from pathlib import Path
from datetime import datetime, timedelta

import requests
import streamlit as st
from PIL import Image

# --- Google GenAI Models import ---------------------------
from google import genai
from google.genai import types

# --- Optional: Natural language date parsing ---------------------------
try:
    import dateparser
except ImportError:
    dateparser = None
    st.warning("⚠️ 'dateparser' not installed. Natural language date filters will be limited.")
# -----------------------------------------------------------------------------

# ----------------------------- Page config -----------------------------------
st.set_page_config(
    page_title="My Bot",
    layout="centered",
    initial_sidebar_state="expanded",
)
# -----------------------------------------------------------------------------

# --- Page Header / Styling ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap');

/* --- Background --- */
body {
    background-color: #A0E7E5 !important;  /* light blue background */
    font-family: 'Comfortaa', cursive !important;
}

/* --- Pixel Title with black fill & outline --- */
.pixel-title {
    font-family: 'Press Start 2P', cursive;
    font-size: 48px;
    font-weight: bold;
    color: black;
    text-shadow:
        2px 0 #FFB6C1,
        -2px 0 #FFB6C1,
        0 2px #FFB6C1,
        0 -2px #FFB6C1,
        1px 1px #FFFFFF,
        -1px -1px #FFFFFF;
    text-align: center;
    margin: 12px 0 4px 0;
}

/* --- Subtitle --- */
.pixel-subtitle {
    text-align: center;
    font-family: 'Comfortaa', cursive;
    font-size: 18px;
    color: #333;
    margin-bottom: 24px;
}

/* --- Twinkling stars --- */
.star {
    display: inline-block;
    width: 6px;
    height: 6px;
    background-color: #FFD700;  /* pastel yellow */
    margin: 1px;
    animation: twinkle 1.5s infinite alternate;
}

@keyframes twinkle {
    0% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.2); }
    100% { opacity: 0.3; transform: scale(1); }
}

/* --- Input boxes / dropdowns --- */
.stTextInput>div>div>input, 
.stTextArea>div>div>textarea, 
.css-1hwfws3, /* dropdown container */
.stSelectbox>div>div>div>select {
    background-color: #fff0f5 !important;
    border: 2px solid #FFB6C1 !important;
    border-radius: 12px !important;
    color: #333 !important;
    font-family: 'Comfortaa', cursive !important;
    padding: 8px !important;
}

/* --- Buttons --- */
.stButton>button {
    background-color: #FFFA87 !important;
    color: #333 !important;
    border: 2px solid #FFB6C1 !important;
    border-radius: 15px !important;
    font-size: 14px !important;
    padding: 12px 20px !important;
}
.stButton>button:hover {
    background-color: #A0E7E5 !important;
    transform: scale(1.05);
}
</style>

<!-- --- Title and stars --- -->
<div style="text-align:center;">
    <div>
        <span class="star"></span>
        <span class="star"></span>
        <span class="star"></span>
        <span class="star"></span>
        <span class="star"></span>
    </div>
    <h1 class="pixel-title">Bearfruit</h1>
    <p class="pixel-subtitle">Your ASU Event Finder Assistant</p>
    <div>
        <span class="star"></span>
        <span class="star"></span>
        <span class="star"></span>
        <span class="star"></span>
        <span class="star"></span>
    </div>
</div>
""", unsafe_allow_html=True)






# ----------------------------- Header image ----------------------------------
try:
    st.image(
        Image.open("Bot.png"),
        caption="Bot Created by Arya Reiland (2025)",
        use_container_width=True,
    )
except Exception as e:
    st.error(f"Error loading image: {e}")

st.markdown("""
<h1 class="pixel-title">Bearfruit</h1>
<p style="text-align:center; font-family:'Comfortaa', cursive;">Your ASU Event Finder Assistant</p>
<!-- Twinkling stars -->
<div class="star"></div>
""", unsafe_allow_html=True)


st.caption("Please be patient, sometimes I take extra time to think.")
# -----------------------------------------------------------------------------

# ----------------------------- Helpers ---------------------------------------
def load_developer_prompt() -> str:
    try:
        with open("identity.txt", encoding="utf-8-sig") as f:
            return f.read()
    except FileNotFoundError:
        st.warning("⚠️ 'identity.txt' not found. Using default prompt.")
        return (
            "You are a helpful assistant. "
            "Be friendly, engaging, and provide clear, concise responses."
        )

def human_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"
# -----------------------------------------------------------------------------

# ----------------------------- Gemini config ---------------------------------
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    system_instructions = load_developer_prompt()

    search_tool = types.Tool(google_search=types.GoogleSearch())

    generation_cfg = types.GenerateContentConfig(
        system_instruction=system_instructions,
        tools=[search_tool],
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        temperature=1.0,
        max_output_tokens=2048,
    )
except Exception as e:
    st.error(
        "Error initialising the Gemini client. "
        "Check your `GEMINI_API_KEY` in Streamlit → Settings → Secrets. "
        f"Details: {e}"
    )
    st.stop()
# -----------------------------------------------------------------------------

# ----------------------------- App state -------------------------------------
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("uploaded_files", [])
st.session_state.setdefault("user_personality", None)
st.session_state.setdefault("quiz_stage", "none")
st.session_state.setdefault("quiz_progress", 0)
# -----------------------------------------------------------------------------

# ----------------------------- Sidebar ---------------------------------------
with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown("### About: Briefly describe your bot here for users.")

    # Model selection
    with st.expander(":material/text_fields_alt: Model Selection", expanded=True):
        selected_model = st.selectbox(
            "Choose a model:",
            options=[
                "gemini-2.5-pro",
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
            ],
            index=2,
        )
        st.caption(f"Selected: **{selected_model}**")

        if "chat" not in st.session_state:
            st.session_state.chat = client.chats.create(
                model=selected_model, config=generation_cfg
            )
        elif getattr(st.session_state.chat, "model", None) != selected_model:
            st.session_state.chat = client.chats.create(
                model=selected_model, config=generation_cfg
            )

    # Clear chat
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.chat_history.clear()
        st.session_state.chat = client.chats.create(
            model=selected_model, config=generation_cfg
        )
        st.toast("Chat cleared.")
        st.rerun()
# -----------------------------------------------------------------------------

# ----------------------------- ASU Event fetch/filter ------------------------
ICS_URL = "https://sundevilcentral.eoss.asu.edu/ics?from_date=15+Sep+2025&to_date=31+Dec+2025&school=arizonau"

def parse_ics(ics_text: str):
    events = []
    current_event = {}
    for line in ics_text.splitlines():
        if line.startswith("BEGIN:VEVENT"):
            current_event = {}
        elif line.startswith("END:VEVENT"):
            if "SUMMARY" in current_event and "DTSTART" in current_event:
                events.append(
                    {
                        "title": current_event.get("SUMMARY", "No title"),
                        "start": current_event.get("DTSTART"),
                        "end": current_event.get("DTEND"),
                        "location": current_event.get("LOCATION", "No location specified"),
                    }
                )
        elif line.startswith("SUMMARY:"):
            current_event["SUMMARY"] = line[len("SUMMARY:") :].strip()
        elif line.startswith("DTSTART"):
            dt_str = line.split(":", 1)[1].strip()
            try:
                current_event["DTSTART"] = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
            except Exception:
                current_event["DTSTART"] = datetime.strptime(dt_str, "%Y%m%d")
        elif line.startswith("DTEND"):
            dt_str = line.split(":", 1)[1].strip()
            try:
                current_event["DTEND"] = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
            except Exception:
                current_event["DTEND"] = datetime.strptime(dt_str, "%Y%m%d")
        elif line.startswith("LOCATION:"):
            current_event["LOCATION"] = line[len("LOCATION:") :].strip()
    return events

def fetch_asu_events():
    try:
        r = requests.get(ICS_URL)
        r.raise_for_status()
        return parse_ics(r.text)
    except Exception as ex:
        st.error(f"Failed to fetch ASU events: {ex}")
        return []

if "asu_events" not in st.session_state:
    st.session_state.asu_events = fetch_asu_events()

# ----------------------------- Personality JSON -----------------------------
JSON_PATH = Path(__file__).with_name("16personalities.json")
personalities: list = []
try:
    if JSON_PATH.exists():
        personalities = json.loads(JSON_PATH.read_text(encoding="utf-8-sig"))
        st.success(f"Loaded {len(personalities)} personality entries!")
    else:
        st.warning("⚠️ '16personalities.json' not found; continuing without personality data.")
except json.JSONDecodeError as e:
    st.error(f"Invalid JSON in {JSON_PATH.name}: {e}. Continuing without personality data.")
except Exception as e:
    st.error(f"Unexpected error loading {JSON_PATH.name}: {e}. Continuing without personality data.")

# ----------------------------- Optional Filters ---------------------------------
st.markdown("### 🎯 Optional Filters for Event Recommendations")

st.info(
    "You don't have to fill these fields. "
    "You can leave them blank and tell the bot about your vibe, personality, or interests organically in the chat."
)

time_frame = st.text_input(
    "Enter a date or time frame (optional, e.g., 'next Friday', 'Sept 20')"
)

vibe = st.selectbox(
    "Select your vibe/mood (optional)",
    options=["Any", "Chill", "Energetic", "Creative", "Social", "Learning"]
)

personality_type = st.text_input(
    "Enter your 16-personality type (optional, e.g., INFP, ESTJ) - If you don't know, no worries! Just ask Bearfruit to identify your personality type."
)

keywords = st.text_input(
    "Enter keywords for your interests (optional, comma-separated, e.g., music, coding, hiking)"
)

# ----------------------------- Chat replay container -------------------------
with st.container():
    for msg in st.session_state.chat_history:
        avatar = "👤" if msg["role"] == "user" else ":material/robot_2:"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["parts"])

# ----------------------------- Files API helper ------------------------------
def _ensure_files_active(files, max_wait_s: float = 12.0):
    deadline = time.time() + max_wait_s
    any_processing = True
    while any_processing and time.time() < deadline:
        any_processing = False
        for i, meta in enumerate(files):
            fobj = meta["file"]
            if getattr(fobj, "state", "") not in ("ACTIVE",):
                any_processing = True
                try:
                    updated = client.files.get(name=fobj.name)
                    files[i]["file"] = updated
                except Exception:
                    pass
        if any_processing:
            time.sleep(0.6)
# -----------------------------------------------------------------------------

# ----------------------------- User Helpers ----------------------------------
def get_personality_text():
    if st.session_state.get("user_personality"):
        return f"User personality: {st.session_state['user_personality']}"
    elif st.session_state.uploaded_files:
        return "User uploaded a personality PDF; infer personality type from it."
    else:
        return "User personality unknown"

def user_said_yes(text: str) -> bool:
    t = text.strip().lower()
    return any(p in t for p in ("yes", "yep", "yeah", "sure", "ok", "okay", "let's do it", "sounds good"))

def user_said_no(text: str) -> bool:
    t = text.strip().lower()
    return any(p in t for p in ("no", "nope", "not now", "skip", "maybe later"))

def seems_like_preference(text: str) -> bool:
    t = text.strip().lower()
    keywords = ("book", "music", "art", "movie", "film", "concert", "sports", "game",
                "coding", "tech", "volunteer", "career", "network", "dance", "outdoor",
                "hiking", "writing", "poetry", "club", "workshop")
    return any(k in t for k in keywords)

# ----------------------------- Chat input / send -----------------------------
if user_prompt := st.chat_input("Message your bot…"):
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    personality_text = get_personality_text()

    if user_said_yes(user_prompt) and st.session_state.quiz_stage in ("none", "offered"):
        st.session_state.quiz_stage = "in_progress"
        st.session_state.quiz_progress = max(st.session_state.quiz_progress, 0)
    elif user_said_no(user_prompt) and st.session_state.quiz_stage in ("none", "offered"):
        st.session_state.quiz_stage = "completed"
    elif seems_like_preference(user_prompt):
        st.session_state.quiz_stage = "completed"
    elif st.session_state.quiz_stage == "none":
        st.session_state.quiz_stage = "offered"

    # ------------------- Event Filtering -------------------
    filtered_events = st.session_state.asu_events

    # Time frame filter if entered
    if time_frame and dateparser:
        parsed_date = dateparser.parse(time_frame)
        if parsed_date:
            filtered_events = [e for e in filtered_events if e["start"].date() == parsed_date.date()]

    # Vibe filter
    if vibe and vibe != "Any":
        filtered_events = [e for e in filtered_events if vibe.lower() in e.get("title", "").lower()]

    # Personality filter
    if personality_type:
        filtered_events = [e for e in filtered_events
                           if personality_type.upper() in (st.session_state.get("user_personality", "").upper() or "")]

    # Keywords filter
    if keywords:
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        filtered_events = [e for e in filtered_events if any(k in e.get("title", "").lower() for k in keyword_list)]

    # Summarize events for bot
    if filtered_events:
        event_texts = []
        for e in filtered_events[:10]:
            start_str = e["start"].strftime("%a, %b %d %I:%M %p")
            end_str = e.get("end").strftime("%I:%M %p") if e.get("end") else "N/A"
            location = e.get("location", "No location specified")
            event_texts.append(f"- {e['title']} ({start_str} – {end_str}) at {location}")
        events_summary = "<h3>Here are upcoming events based on your filters:</h3>" + "<br>".join(event_texts)
    else:
        events_summary = "No events match your criteria for the next week."

    # ------------------- Chat Prompt -------------------
    state_directive = f"""
APP_STATE:
- quiz_stage: {st.session_state.quiz_stage}
- quiz_progress: {st.session_state.quiz_progress}
"""
    user_prompt_with_events = f"""
User message: {user_prompt}

Personality context: {personality_text}

Personality database: {json.dumps(personalities)}

Upcoming events (next week / filtered): {events_summary}

{state_directive}

Instructions:
1. Recommend events that best match the user's preferences and personality.
2. If the user's personality is unknown **and** quiz_stage == 'none', invite a short quiz; otherwise follow APP_STATE above (do not re-offer).
3. Be friendly and concise.
"""

    with st.chat_message("assistant", avatar=":material/robot_2:"):
        try:
            contents_to_send = [types.Part(text=user_prompt_with_events)]
            if st.session_state.uploaded_files:
                _ensure_files_active(st.session_state.uploaded_files)
                for meta in st.session_state.uploaded_files:
                    contents_to_send.append(meta["file"])

            response = st.session_state.chat.send_message(contents_to_send)
            full_response = response.text if hasattr(response, "text") else str(response)

            st.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "parts": full_response})

        except Exception as e:
            st.error(f"❌ Error from Gemini: {e}")


# --- Display chat using styled bubbles ---
for msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
    st.markdown(
        f'<div class="chat-container"><div class="chat-bubble {bubble_class}">{msg["parts"]}</div></div>',
        unsafe_allow_html=True
    )



