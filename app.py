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

# ----------------------------- Header Image ------------------------
try:
    header_img = Image.open("Bot.png")  # replace with your file path
    st.image(header_img, use_container_width=True)
except FileNotFoundError:
    st.warning("Header image not found. Place 'header_image.png' in the app folder.")

# ------ CSS
st.markdown("""
<style>
/* --- Background --- */
.stApp {
    background-color: #2E2E2E !important;  /* dark grey */
}

/* --- Bearfruit Title --- */
.pixel-title {
    font-family: 'Press Start 2P', cursive;
    font-size: 64px;
    color: #FFCDEB;  /* light pink fill */
    text-align: center;
    text-shadow: 
        -2px -2px 0 #000,  
         2px -2px 0 #000,
        -2px  2px 0 #000,
         2px  2px 0 #000; /* black outline */
    margin-bottom: 20px;
}

/* --- "Choose your model" label --- */
label[for*="model"] {
    color: black !important;
    font-weight: bold;
}

/* --- Sidebar selectboxes (vibe, model, etc.) --- */
[data-testid="stSidebar"] .stSelectbox>div>div>div[role="combobox"] {
    background-color: #D9FEC9 !important; /* light green */
    color: #333 !important;
    border: 2px solid #E5DBFF !important; /* lavender border */
    border-radius: 6px !important;
}

/* dropdown list options */
[data-testid="stSidebar"] .stSelectbox>div>div>div[role="listbox"] {
    background-color: #D9FEC9 !important;
    color: #333 !important;
}

/* --- Ensure label text is visible --- */
label[for*="vibe"], label[for*="model"] {
    color: black !important;
    font-weight: bold;
}

/* --- Top bar --- */
header[data-testid="stHeader"] {
    background-color: #FFCDEB !important; /* light pink */
}
</style>
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
    selected_model = st.selectbox(
        "Choose a model:",
        options=[
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ],
        index=2,
    )
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

# ----------------------------- Optional Filters -----------------------------
st.markdown("### 🎯 Optional Filters for Event Recommendations")
st.info(
    "You don't have to fill these fields. "
    "You can leave them blank and tell the bot about your vibe, personality, or interests organically in the chat."
)

time_frame = st.text_input("Enter a date or time frame (optional, e.g., 'next Friday', 'Sept 20')")
vibe = st.selectbox("Select your vibe/mood (optional)", options=["Any", "Chill", "Energetic", "Creative", "Social", "Learning"])
personality_type = st.text_input("Enter your 16-personality type (optional, e.g., INFP, ESTJ)")
keywords = st.text_input("Enter keywords for your interests (optional, comma-separated, e.g., music, coding, hiking)")

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
