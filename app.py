# BearFruit
# Copyright (c) 2025 Arya Reiland

# ----------------------------- Imports -----------------------------
import io, time, json
from pathlib import Path
from datetime import datetime, timedelta
import requests
import streamlit as st
from PIL import Image
from dateutil.parser import parse as parse_date

from google import genai
from google.genai import types

# ----------------------------- Page config ------------------------
st.set_page_config(
    page_title="BearFruit",
    page_icon="🐻",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- Header Image ---
try:
    header_img = Image.open("Bot.png")
    st.image(header_img, use_container_width=True, output_format="PNG")
except FileNotFoundError:
    st.warning("Bot.png not found. Header image disabled.")

# --- CSS & Theme ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap');
body { font-family: 'Comfortaa', cursive; background: linear-gradient(135deg, #FFB6C1, #A0E7E5); color: #333; overflow-x: hidden; }
[data-testid="stSidebar"] { background-color: #FFF0F5 !important; color: #333; border-right: 2px solid #FFD6E8; }
h1.title { text-align: center; font-family: 'Comfortaa', cursive; font-size: 48px; }
.subtitle { text-align:center; font-family:'Comfortaa', cursive; font-size:18px; margin-bottom: 20px; color: #FFF; }
.chat-bubble { max-width: 70%; padding: 12px 16px; margin: 8px 0; border-radius: 20px; font-family: 'Comfortaa', cursive; font-size: 14px; border: 2px solid; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
.user-bubble { background-color: #FFFAF0; border-color: #FFB6C1; align-self: flex-end; }
.bot-bubble { background-color: #E0F7FA; border-color: #A0E7E5; align-self: flex-start; }
.chat-container { display: flex; flex-direction: column; }
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div[role="listbox"], select, option { background-color: #FFFAF0 !important; border: 2px solid #FFB6C1; border-radius: 12px; color: #333; font-family: 'Comfortaa', cursive; padding: 8px; }
.stSelectbox>label { color: #FFF !important; }
.stButton>button { background-color: #FFFA87 !important; color: #333 !important; border: 2px solid #FFB6C1 !important; border-radius: 15px !important; font-size: 14px; padding: 12px 20px; transition: all 0.2s ease-in-out; }
.stButton>button:hover { background-color: #A0E7E5 !important; transform: scale(1.05); }
</style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("""
<h1 class="title">
  <span style="color:#FFE87F;">𖡼</span>
  <span style="color:#ADD8E6;">𖤣</span>
  <span style="color:#90EE90;">𖥧</span>
  <span style="color:#FFE87F;">Bear</span><span style="color:#FF6B81;">Fruit</span>
  <span style="color:#90EE90;">𖥧</span>
  <span style="color:#ADD8E6;">𖤣</span>
  <span style="color:#90EE90;">𖡼</span>
</h1>
<p class="subtitle">Your ASU Event Finder</p>
""", unsafe_allow_html=True)

# ----------------------------- Helpers -----------------------------
def load_developer_prompt() -> str:
    try:
        with open("identity.txt", encoding="utf-8-sig") as f:
            return f.read()
    except FileNotFoundError:
        st.warning("⚠️ 'identity.txt' not found. Using default prompt.")
        return "You are a helpful assistant. Be friendly, engaging, and provide clear, concise responses."

# ----------------------------- Gemini config --------------------------
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    system_instructions = load_developer_prompt()
    generation_cfg = types.GenerateContentConfig(
        system_instruction=system_instructions,
        temperature=1.0,
        max_output_tokens=512,  # shorter output for safety
    )
except Exception as e:
    st.error(f"Error initialising Gemini client: {e}")
    st.stop()

# ----------------------------- App state -----------------------------
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("asu_events", [])
st.session_state.setdefault("user_personality", None)

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.title("⚙️ Controls")
    selected_model = st.selectbox(
        "Choose a model:",
        options=["gemini-2.5-pro","gemini-2.5-flash","gemini-2.5-flash-lite"],
        index=2,
    )
    if "chat" not in st.session_state or getattr(st.session_state.chat, "model", None) != selected_model:
        st.session_state.chat = client.chats.create(model=selected_model, config=generation_cfg)

    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.chat_history.clear()
        st.session_state.chat = client.chats.create(model=selected_model, config=generation_cfg)
        st.toast("Chat cleared.")
        st.experimental_rerun()

# ----------------------------- Filters -----------------------------
st.markdown("### 🎯 Optional Filters")
time_frame = st.text_input("Enter a date/time frame (optional)")
vibe = st.selectbox("Select your vibe/mood", ["Any","Chill","Energetic","Creative","Social","Learning"])
personality_type = st.text_input("Enter your 16-personality type (optional)")
keywords = st.text_input("Enter keywords (comma-separated)")

# ----------------------------- Event Fetch & Cache -----------------------------
ICS_URL = "https://sundevilcentral.eoss.asu.edu/ics?from_date=15+Sep+2025&to_date=31+Dec+2025&school=arizonau"

@st.cache_data(show_spinner=False)
def fetch_asu_events():
    try:
        r = requests.get(ICS_URL)
        r.raise_for_status()
        events = []
        current_event = {}
        for line in r.text.splitlines():
            if line.startswith("BEGIN:VEVENT"):
                current_event = {}
            elif line.startswith("END:VEVENT"):
                if "SUMMARY" in current_event and "DTSTART" in current_event:
                    events.append({
                        "title": current_event.get("SUMMARY","No title"),
                        "start": current_event.get("DTSTART"),
                        "end": current_event.get("DTEND"),
                        "location": current_event.get("LOCATION","No location")
                    })
            elif line.startswith("SUMMARY:"): current_event["SUMMARY"]=line[len("SUMMARY:"):].strip()
            elif line.startswith("DTSTART"):
                dt_str=line.split(":",1)[1].strip()
                try: current_event["DTSTART"]=datetime.strptime(dt_str,"%Y%m%dT%H%M%S")
                except: current_event["DTSTART"]=datetime.strptime(dt_str,"%Y%m%d")
            elif line.startswith("DTEND"):
                dt_str=line.split(":",1)[1].strip()
                try: current_event["DTEND"]=datetime.strptime(dt_str,"%Y%m%dT%H%M%S")
                except: current_event["DTEND"]=datetime.strptime(dt_str,"%Y%m%d")
            elif line.startswith("LOCATION:"): current_event["LOCATION"]=line[len("LOCATION:"):].strip()
        return events
    except Exception as ex:
        st.error(f"Failed to fetch ASU events: {ex}")
        return []

if not st.session_state.asu_events:
    st.session_state.asu_events = fetch_asu_events()

# ----------------------------- Event Filtering -----------------------------
@st.cache_data(show_spinner=False)
def filter_events(events, user_msg, time_frame, vibe, personality_type, keywords):
    now = datetime.now()
    start_dt, end_dt = now, now+timedelta(days=7)
    if time_frame:
        try:
            dt=parse_date(time_frame,fuzzy=True)
            start_dt, end_dt = dt, dt+timedelta(days=1)
        except: pass

    filtered=[]
    for e in events:
        title=e["title"].lower()
        loc=e.get("location","").lower()
        if start_dt <= e["start"] <= end_dt:
            if user_msg.lower() in title or user_msg.lower() in loc:
                filtered.append(e)
            elif keywords:
                if any(kw.strip().lower() in title+loc for kw in keywords.split(",")):
                    filtered.append(e)
    return filtered[:10]

# ----------------------------- Chat -----------------------------
with st.container():
    for msg in st.session_state.chat_history:
        avatar="🍓" if msg["role"]=="user" else "🐻"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["parts"])

if user_prompt := st.chat_input("Message your bot…"):
    st.session_state.chat_history.append({"role":"user","parts":user_prompt})
    with st.chat_message("user", avatar="👤"): st.markdown(user_prompt)

    # --- Filter events ---
    filtered_events = filter_events(
        st.session_state.asu_events, user_prompt, time_frame, vibe, personality_type, keywords
    )

    if filtered_events:
        events_summary = "\n".join([
            f"- {e['title']} at {e['location']} on {e['start'].strftime('%b %d %Y %H:%M')}" 
            for e in filtered_events
        ])
        bot_reply = f"Here are some ASU events that match your preferences:\n\n{events_summary}"
    else:
        bot_reply = "No matching events found based on your preferences."

    # Optional: Gemini adds friendly commentary
    try:
        response = st.session_state.chat.send_message(f"Make this reply more friendly:\n{bot_reply}")
        if hasattr(response, "result") and response.result:
            content_blocks = getattr(response.result[0], "content", [])
            if content_blocks:
                gemini_text = "".join(getattr(block, "text", "") for block in content_blocks)
                if gemini_text.strip():
                    bot_reply = gemini_text
    except Exception:
        pass  # fallback to filtered events text

    st.session_state.chat_history.append({"role":"assistant","parts":bot_reply})
    with st.chat_message("assistant", avatar="🐻"): st.markdown(bot_reply)

