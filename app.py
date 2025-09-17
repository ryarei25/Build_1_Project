# BearFruit
# Copyright (c) 2025 Arya Reiland

# ----------------------------- Imports -----------------------------
import io
import time
import json
import requests
from pathlib import Path
from datetime import datetime
import streamlit as st
from PIL import Image

# Google GenAI Models import
from google import genai
from google.genai import types

# Optional: Natural language date parsing
try:
    import dateparser
except ImportError:
    dateparser = None
    st.warning("⚠️ 'dateparser' not installed. Natural language date filters will be limited.")

# ----------------------------- Page config -----------------------------
st.set_page_config(
    page_title="Bearfruit",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ----------------------------- CSS -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

body {
    font-family: 'Comfortaa', cursive;
    background: #CCE7FF;
    color: #333;
    overflow-x: hidden;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #E5DBFF;
    color: #333;
}

/* Top header bar */
header {
    background-color: #FFCDEB !important;
}

/* Pixelated Bearfruit Title */
.pixel-title {
    text-align: center;
    font-size: 80px;
    font-family: 'Press Start 2P', cursive;
    color: #CCE7FF; 
    text-shadow:
        2px 2px #000,
        4px 4px #000,
        6px 6px #000;
    position: relative;
}

/* Static Twinkling Pixel Stars */
.star {
    position: absolute;
    width: 3px;
    height: 3px;
    color: #FFE4A4;
    animation: twinkle 2s infinite;
}
@keyframes twinkle {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
}

/* Chat bubbles / retro window boxes */
.chat-bubble {
    max-width: 70%;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 0;
    font-family: 'Comfortaa', cursive;
    font-size: 14px;
    background-color: #D9FEC9;
    border: 2px solid #333;
    box-shadow: 3px 3px #888888;
}

/* Buttons */
.stButton>button {
    background-color: #FFE4A4 !important;
    color: #333 !important;
    border: 2px solid #333 !important;
    border-radius: 5px !important;
    font-size: 14px;
    padding: 8px 12px;
    transition: all 0.2s ease-in-out;
}

.stButton>button:hover {
    background-color: #D9FEC9 !important;
    transform: scale(1.05);
}

/* Inputs, textareas, selectboxes */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>div {
    background-color: #D9FEC9 !important;
    border: 2px solid #333 !important;
    border-radius: 0px;
    color: #333;
    padding: 6px;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 10px;
}
::-webkit-scrollbar-thumb {
    background: #E5DBFF;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------- Header / Title -----------------------------
# Pixel stars container
st.markdown("""
<div style="position: relative; height: 120px;">
    <div class="star" style="top: 10px; left: 20px;"></div>
    <div class="star" style="top: 50px; left: 200px;"></div>
    <div class="star" style="top: 30px; left: 400px;"></div>
    <div class="star" style="top: 80px; left: 600px;"></div>
    <div class="star" style="top: 20px; left: 700px;"></div>
    <h1 class="pixel-title">Bearfruit</h1>
</div>
<p style="text-align:center; font-family:'Comfortaa', cursive;">Your ASU Event Finder Assistant</p>
<p style="text-align:center; font-family:'Comfortaa', cursive; font-size:12px;">Please be patient, sometimes I take extra time to think.</p>
""", unsafe_allow_html=True)

# ----------------------------- Helpers -----------------------------
def load_developer_prompt() -> str:
    try:
        with open("identity.txt", encoding="utf-8-sig") as f:
            return f.read()
    except FileNotFoundError:
        st.warning("⚠️ 'identity.txt' not found. Using default prompt.")
        return "You are a helpful assistant. Be friendly, engaging, and provide clear, concise responses."

# ----------------------------- Gemini / Model setup -----------------------------
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
    st.error(f"Error initializing Gemini client: {e}")
    st.stop()

# ----------------------------- Session state -----------------------------
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
        if "chat" not in st.session_state:
            st.session_state.chat = client.chats.create(model=selected_model, config=generation_cfg)
        elif getattr(st.session_state.chat, "model", None) != selected_model:
            st.session_state.chat = client.chats.create(model=selected_model, config=generation_cfg)
    # Clear chat
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.chat_history.clear()
        st.session_state.chat = client.chats.create(model=selected_model, config=generation_cfg)
        st.toast("Chat cleared.")
        st.rerun()

# ----------------------------- Chat Input / Display -----------------------------
if user_prompt := st.chat_input("Message your bot…"):
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)
    # send to Gemini
    try:
        contents_to_send = [types.Part(text=user_prompt)]
        response = st.session_state.chat.send_message(contents_to_send)
        full_response = response.text if hasattr(response, "text") else str(response)
        st.session_state.chat_history.append({"role": "assistant", "parts": full_response})
        with st.chat_message("assistant", avatar=":material/robot_2:"):
            st.markdown(full_response)
    except Exception as e:
        st.error(f"❌ Error from Gemini: {e}")

# --- Display chat bubbles
for msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
    st.markdown(f'<div class="chat-container"><div class="chat-bubble {bubble_class}">{msg["parts"]}</div></div>', unsafe_allow_html=True)




