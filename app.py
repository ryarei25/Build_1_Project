# BearFruit
# Copyright (c) 2025 Arya Reiland

# ----------------------------- Imports -----------------------------
import io
import time
import json
from pathlib import Path
from datetime import datetime

import requests
import streamlit as st
from PIL import Image

# --- Google GenAI Models import ---------------------------
from google import genai
from google.genai import types

# ----------------------------- Page config ------------------------
st.set_page_config(
    page_title="Bearfruit",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ----------------------------- CSS & Theme ------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Comfortaa:wght@400;700&display=swap');

/* --- Background & general body --- */
body {
    font-family: 'Comfortaa', cursive;
    background: linear-gradient(135deg, #C6D7E6, #FFB9B7);
    color: #333;
    overflow-x: hidden;
}

/* --- Sidebar --- */
[data-testid="stSidebar"] {
    background-color: #D1DDB4 !important;
    color: #333;
    border-right: 2px solid #D8C5DD;
}

/* --- Top bar (menu) --- */
header {
    background-color: #CCE7FF !important;
}

/* --- Pixelated Bearfruit Title --- */
.pixel-title-container {
    position: relative;
    text-align: center;
    margin-bottom: 20px;
}
.pixel-title {
    font-family: 'Press Start 2P', cursive;
    font-size: 48px;
    color: #000; /* black inside */
    text-shadow:
        2px 2px #EBB7FB,
        4px 4px #FFE4A4,
        6px 6px #D1DDB4;
    display: inline-block;
    z-index: 2;
}

/* --- Pixel stars --- */
.star {
    position: absolute;
    width: 2px;
    height: 2px;
    background-color: #FFE4A4;
    animation: twinkle 2s infinite;
}
@keyframes twinkle {
    0%,100% {opacity:0.2;}
    50% {opacity:1;}
}

/* --- Chat bubbles --- */
.chat-bubble {
    max-width: 70%;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 4px;
    font-family: 'Comfortaa', cursive;
    font-size: 14px;
    border: 2px solid;
    box-shadow: 2px 2px 0 #D8C5DD;
}

.user-bubble {
    background-color: #CCE7FF;
    border-color: #C6D7E6;
    align-self: flex-end;
}

.bot-bubble {
    background-color: #FFB9B7;
    border-color: #D8C5DD;
    align-self: flex-start;
}

/* --- Chat container --- */
.chat-container {
    display: flex;
    flex-direction: column;
}

/* --- Inputs & selectbox --- */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>div[role="listbox"] {
    background-color: #FFF1A7 !important;
    border: 2px solid #D8C5DD;
    border-radius: 6px;
    color: #333;
    font-family: 'Comfortaa', cursive;
    padding: 6px;
}

/* --- Buttons --- */
.stButton>button {
    background-color: #D8C5DD !important;
    color: #333 !important;
    border: 2px solid #C6D7E6 !important;
    border-radius: 4px !important;
    font-size: 14px;
    padding: 10px 16px;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    background-color: #CCE7FF !important;
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# ----------------------------- Star field HTML ------------------------
st.markdown("""
<div class="pixel-title-container">
    <h1 class="pixel-title">Bearfruit</h1>
</div>
<script>
const container = document.querySelector('.pixel-title-container');
for(let i=0;i<60;i++){
    const star = document.createElement('div');
    star.classList.add('star');
    star.style.top = Math.random()*50 + 'px';
    star.style.left = Math.random()*container.offsetWidth + 'px';
    container.appendChild(star);
}
</script>
<p style="text-align:center; font-family:'Comfortaa', cursive;">Your ASU Event Finder Assistant</p>
""", unsafe_allow_html=True)

# ----------------------------- Helpers -----------------------------
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

# ----------------------------- Gemini config --------------------------
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

# ----------------------------- App state -----------------------------
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("uploaded_files", [])
st.session_state.setdefault("user_personality", None)
st.session_state.setdefault("quiz_stage", "none")
st.session_state.setdefault("quiz_progress", 0)

# ----------------------------- Sidebar -----------------------------
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

    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.chat_history.clear()
        st.session_state.chat = client.chats.create(
            model=selected_model, config=generation_cfg
        )
        st.toast("Chat cleared.")
        st.rerun()

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

# ----------------------------- Optional Filters -----------------------------
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
    "Enter your 16-personality type (optional, e.g., INFP, ESTJ)"
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

# ----------------------------- Chat input / send -----------------------------
if user_prompt := st.chat_input("Message your bot…"):
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)
