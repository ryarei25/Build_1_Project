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
    page_title="BearFruit",
    page_icon="🐻",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- Header Image ---
header_img = Image.open("Bot.png")
st.image(header_img, use_container_width=True, output_format="PNG")

# ----------------------------- CSS & Theme ------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap');

body {
    font-family: 'Comfortaa', cursive;
    background: linear-gradient(135deg, #FFB6C1, #A0E7E5);
    color: #333;
    overflow-x: hidden;
}

/* --- Sidebar --- */
[data-testid="stSidebar"] {
    background-color: #FFF0F5 !important;  
    color: #333;
    border-right: 2px solid #FFD6E8;
}

/* --- Title --- */
h1.title {
    text-align: center;
    font-family: 'Comfortaa', cursive;
    font-size: 48px;
    color: #FF6B81;
    text-shadow: 2px 2px #FFD3E0;
    margin-bottom: 0;
}
.subtitle {
    text-align:center;
    font-family:'Comfortaa', cursive;
    font-size:18px;
    margin-bottom: 20px;
    color: #444;
}

/* --- Chat bubbles --- */
.chat-bubble {
    max-width: 70%;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 20px;
    font-family: 'Comfortaa', cursive;
    font-size: 14px;
    border: 2px solid;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}
.user-bubble {
    background-color: #FFFAF0;
    border-color: #FFB6C1;
    align-self: flex-end;
}
.bot-bubble {
    background-color: #E0F7FA;
    border-color: #A0E7E5;
    align-self: flex-start;
}
.chat-container {
    display: flex;
    flex-direction: column;
}

/* --- Inputs --- */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>div[role="listbox"],
select, option {
    background-color: #fff0f5 !important;  
    border: 2px solid #FFB6C1;
    border-radius: 12px;
    color: #333;
    font-family: 'Comfortaa', cursive;
    padding: 8px;
}

/* --- Buttons --- */
.stButton>button {
    background-color: #FFFA87 !important;
    color: #333 !important;
    border: 2px solid #FFB6C1 !important;
    border-radius: 15px !important;
    font-size: 14px;
    padding: 12px 20px;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    background-color: #A0E7E5 !important;
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("""
<h1 class="title"> ⋆｡ﾟ☁︎｡⋆｡ ﾟ☾ ﾟ｡⋆ BearFruit</h1>
<p class="subtitle">Your Personalized ASU Event Finder </p>
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
        avatar = "🍓" if msg["role"] == "user" else "🐻"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["parts"])

# ----------------------------- Chat input / send -----------------------------
if user_prompt := st.chat_input("Message your bot…"):
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)
