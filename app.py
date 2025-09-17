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
    st.image(header_img, use_column_width=True)
except FileNotFoundError:
    st.warning("Header image not found. Place 'header_image.png' in the app folder.")

# ----------------------------- CSS & Theme ------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Comfortaa:wght@400;700&display=swap');

/* --- Background & general body --- */
body {
    font-family: 'Comfortaa', cursive;
    background-color: #CCE7FF;
    color: #333;
    overflow-x: hidden;
}

/* --- Sidebar --- */
[data-testid="stSidebar"] {
    background-color: #E5DBFF !important;
    color: #333;
    border-right: 2px solid #D8C5DD;
}

/* --- Top bar (menu) --- */
header {
    background-color: #FFCDEB !important;
}

/* --- Pixelated Bearfruit Title --- */
.pixel-title-container {
    position: relative;
    text-align: center;
    margin-bottom: 10px;
}
.pixel-title {
    font-family: 'Press Start 2P', cursive;
    font-size: 72px;
    color: #000; /* black inside */
    text-shadow:
        2px 2px #EBC7FB,
        4px 4px #FFE4A4,
        6px 6px #D9FEC9;
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

/* --- Subtitle --- */
.subtitle {
    text-align:center;
    font-family:'Comfortaa', cursive;
    font-size:18px;
    margin-bottom: 20px;
    color: #333;
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
    border-color: #D9FEC9;
    align-self: flex-end;
}

.bot-bubble {
    background-color: #FFCDEB;
    border-color: #EBC7FB;
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
    background-color: #D9FEC9 !important;
    border: 2px solid #D8C5DD;
    border-radius: 6px;
    color: #333;
    font-family: 'Comfortaa', cursive;
    padding: 6px;
}

/* --- Buttons --- */
.stButton>button {
    background-color: #FFE4A4 !important;
    color: #333 !important;
    border: 2px solid #EBC7FB !important;
    border-radius: 4px !important;
    font-size: 14px;
    padding: 10px 16px;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    background-color: #FFCDEB !important;
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
    star.style.top = Math.random()*60 + 'px';
    star.style.left = Math.random()*container.offsetWidth + 'px';
    container.appendChild(star);
}
</script>
<p class="subtitle">Your ASU Event Finder Assistant</p>
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
