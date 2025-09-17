# BearFruit
# Copyright (c) 2025 Arya Reiland

import io, json, time
from pathlib import Path
from datetime import datetime, timedelta

import requests
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# ---------------- Page config ----------------
st.set_page_config(
    page_title="BearFruit",
    page_icon="🐻",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------- Header ----------------
try:
    header_img = Image.open("Bot.png")
    st.image(header_img, use_container_width=True, output_format="PNG")
except:
    st.warning("Header image not found.")

st.markdown("<h1 style='text-align:center'>BearFruit: Your ASU Event Finder</h1>", unsafe_allow_html=True)
st.caption("Chat with your assistant below…")

# ---------------- Helpers ----------------
def load_developer_prompt() -> str:
    try:
        return Path("identity.txt").read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return "You are a helpful assistant. Be friendly, concise, and clear."

def parse_ics(ics_text: str):
    events, current = [], {}
    for line in ics_text.splitlines():
        if line.startswith("BEGIN:VEVENT"): current = {}
        elif line.startswith("END:VEVENT") and "SUMMARY" in current and "DTSTART" in current:
            events.append({
                "title": current.get("SUMMARY", "No title"),
                "start": current.get("DTSTART"),
                "end": current.get("DTEND"),
                "location": current.get("LOCATION", "No location specified")
            })
        elif line.startswith("SUMMARY:"): current["SUMMARY"] = line.split(":",1)[1]
        elif line.startswith("DTSTART"):
            dt = line.split(":",1)[1]
            try: current["DTSTART"] = datetime.strptime(dt, "%Y%m%dT%H%M%S")
            except: current["DTSTART"] = datetime.strptime(dt, "%Y%m%d")
        elif line.startswith("DTEND"):
            dt = line.split(":",1)[1]
            try: current["DTEND"] = datetime.strptime(dt, "%Y%m%dT%H%M%S")
            except: current["DTEND"] = datetime.strptime(dt, "%Y%m%d")
        elif line.startswith("LOCATION:"): current["LOCATION"] = line.split(":",1)[1]
    return events

def fetch_asu_events():
    ICS_URL = "https://sundevilcentral.eoss.asu.edu/ics?from_date=15+Sep+2025&to_date=31+Dec+2025&school=arizonau"
    try:
        r = requests.get(ICS_URL)
        r.raise_for_status()
        return parse_ics(r.text)
    except:
        st.error("Failed to fetch ASU events.")
        return []

# ---------------- Gemini client ----------------
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    system_instructions = load_developer_prompt()
    generation_cfg = types.GenerateContentConfig(
        system_instruction=system_instructions,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        temperature=1.0,
        max_output_tokens=2048,
    )
except Exception as e:
    st.error(f"Error initializing Gemini: {e}")
    st.stop()

# ---------------- App state ----------------
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("quiz_stage", "none")
st.session_state.setdefault("quiz_progress", 0)
st.session_state.setdefault("asu_events", fetch_asu_events())

# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("⚙️ Controls")
    selected_model = st.selectbox("Choose model", ["gemini-2.5-pro","gemini-2.5-flash","gemini-2.5-flash-lite"], index=2)
    if "chat" not in st.session_state or getattr(st.session_state.chat, "model", None) != selected_model:
        st.session_state.chat = client.chats.create(model=selected_model, config=generation_cfg)
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.chat_history.clear()
        st.session_state.chat = client.chats.create(model=selected_model, config=generation_cfg)
        st.rerun()

# ---------------- Event filters ----------------
time_frame = st.text_input("Enter date/time frame (optional, e.g., 'next Friday')")
vibe = st.selectbox("Your vibe (optional)", ["Any", "Chill", "Energetic", "Creative", "Social", "Learning"])
personality_type = st.text_input("Personality type (optional, e.g., INFP, ESTJ)")
keywords = st.text_input("Keywords (optional, comma-separated)")

def filter_events(events, prompt="", days_ahead=7):
    now = datetime.now()
    end_date = now + timedelta(days=days_ahead)
    filtered = []
    for e in events:
        if now <= e["start"] <= end_date and (
            prompt.lower() in e["title"].lower() or prompt.lower() in e.get("location","").lower()
        ):
            filtered.append(e)
    return filtered[:10]

# ---------------- Chat display ----------------
for msg in st.session_state.chat_history:
    avatar = "🍓" if msg["role"]=="user" else "🐻"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["parts"])

# ---------------- Chat input ----------------
if user_prompt := st.chat_input("Message your bot…"):
    st.session_state.chat_history.append({"role":"user","parts":user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    # Prepare event summary for bot
    filtered = filter_events(st.session_state.asu_events, prompt=user_prompt)
    if filtered:
        event_texts = [f"- {e['title']} ({e['start'].strftime('%b %d %I:%M %p')}) at {e['location']}" for e in filtered]
        events_summary = "<br>".join(event_texts)
    else:
        events_summary = "No matching events in your timeframe."

    # Build bot prompt
    bot_prompt = f"""
User message: {user_prompt}
Vibe: {vibe}, Personality: {personality_type}, Keywords: {keywords}
Upcoming events (next week): {events_summary}
Please respond with friendly, concise suggestions and event recommendations.
"""

    # Send to Gemini
    try:
        contents = [types.Part(text=bot_prompt)]
        response = st.session_state.chat.send_message(contents)
        full_response = response.text if hasattr(response, "text") else str(response)
        st.session_state.chat_history.append({"role":"assistant","parts":full_response})
        with st.chat_message("assistant", avatar=":material/robot_2:"):
            st.markdown(full_response)
    except Exception as e:
        st.error(f"⚠️ Error with Gemini chat: {e}")
