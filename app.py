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
# -----------------------------------------------------------------------------

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

# ----------------------------- Header image ----------------------------------
try:
    st.image(
        Image.open("Bot.png"),
        caption="Bot Created by Arya Reiland (2025)",
        use_container_width=True,
    )
except Exception as e:
    st.error(f"Error loading image: {e}")

st.markdown(
    "<h1 style='text-align: center;'>Bearfruit, Your ASU Event Finder Assistant</h1>",
    unsafe_allow_html=True,
)
st.caption("Please be patient, sometimes I take extra time to think.")
# -----------------------------------------------------------------------------

# ----------------------------- Helpers ---------------------------------------
def load_developer_prompt() -> str:
    """Load system instructions from identity.txt if present; fallback to a default."""
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

# Optional: Natural language filter with dateparser
date_filter = st.text_input("Enter a date or time frame (e.g. 'next Friday', 'September 20'):")

if date_filter and dateparser:
    parsed_date = dateparser.parse(date_filter)
    if parsed_date:
        filtered_events = [
            e for e in st.session_state.asu_events
            if e["start"].date() == parsed_date.date()
        ]
    else:
        st.warning(f"Could not parse '{date_filter}' into a date.")
        filtered_events = st.session_state.asu_events
else:
    filtered_events = st.session_state.asu_events
# -----------------------------------------------------------------------------

