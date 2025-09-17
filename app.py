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
    page_title="Bearfruit",
    layout="centered",
    initial_sidebar_state="expanded",
)
# -----------------------------------------------------------------------------

# --- CSS for theme and retro flair ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

/* Body background */
body {
    font-family: 'Comfortaa', cursive;
    background: linear-gradient(135deg, #CCE7FF, #FFCDEB);
    color: #222;
    overflow-x: hidden;
}

/* Pixelated Bearfruit title */
.pixel-title {
    text-align: center;
    font-family: 'Press Start 2P', cursive;
    font-size: 72px;
    color: #FFCDEB;
    -webkit-text-stroke: 3px #000; /* black outline for readability */
    position: relative;
}

/* Twinkling pixel stars */
.star {
    position: absolute;
    width: 3px;
    height: 3px;
    color: #EBE4A4; /* pastel yellow */
    font-size: 20px;
    animation: twinkle 2s infinite alternate;
}

@keyframes twinkle {
    0% {opacity: 0.2;}
    50% {opacity: 1;}
    100% {opacity: 0.2;}
}

/* Chat bubbles */
.chat-bubble {
    max-width: 70%;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 12px;
    font-family: 'Comfortaa', cursive;
    font-size: 14px;
    box-shadow: 0 0 8px rgba(0,0,0,0.2);
}

.user-bubble {
    background-color: #D9FEC9;
    border: 2px solid #CCE7FF;
    align-self: flex-end;
}

.bot-bubble {
    background-color: #FFCDEB;
    border: 2px solid #E5DBFF;
    align-self: flex-start;
}

/* Chat container */
.chat-container {
    display: flex;
    flex-direction: column;
}

/* Buttons */
.stButton>button {
    background-color: #FFE4A4 !important;
    color: #222 !important;
    border: 2px solid #FFCDEB !important;
    border-radius: 5px !important;
    font-family: 'Press Start 2P', cursive;
    font-size: 12px;
    padding: 10px 16px;
    transition: all 0.2s ease-in-out;
}

.stButton>button:hover {
    background-color: #CCE7FF !important;
    transform: scale(1.05);
}

/* Inputs */
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
    background-color: #D9FEC9;
    border: 2px solid #E5DBFF;
    border-radius: 4px;
    color: #222;
    font-family: 'Comfortaa', cursive;
    padding: 8px;
}

/* Sidebar */
.css-1d391kg [data-testid="stSidebar"] {
    background-color: #E5DBFF !important;
    color: #222 !important;
}

.css-1d391kg .css-1v3fvcr {
    background-color: #D9FEC9 !important;
    border: 2px solid #222 !important;
    border-radius: 4px !important;
    padding: 10px !important;
    color: #222 !important;
    font-family: 'Press Start 2P', cursive;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------- Header Title and Stars ------------------------
st.markdown("""
<div style="position: relative;">
    <h1 class="pixel-title">Bearfruit</h1>
</div>
<p style="text-align:center; font-family:'Comfortaa', cursive;">Your ASU Event Finder Assistant</p>
<p style="text-align:center; font-family:'Comfortaa', cursive; font-size:12px;">Please be patient, sometimes I take extra time to think.</p>
""", unsafe_allow_html=True)

# ----------------------------- App State -------------------------------------
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("uploaded_files", [])
st.session_state.setdefault("user_personality", None)
st.session_state.setdefault("quiz_stage", "none")
st.session_state.setdefault("quiz_progress", 0)

# ----------------------------- Sidebar ---------------------------------------
with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown("### About: Briefly describe your bot here for users.")
    
    # Example: model selection box
    selected_model = st.selectbox(
        "Choose a model:",
        options=["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
        index=2
    )

    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.chat_history.clear()
        st.toast("Chat cleared.")

# ----------------------------- Chat input / send -----------------------------
if user_prompt := st.chat_input("Message your bot…"):
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    # Example assistant response
    response_text = "Hello! I'm Bearfruit, your event-finding assistant."
    st.session_state.chat_history.append({"role": "assistant", "parts": response_text})
    with st.chat_message("assistant", avatar=":material/robot_2:"):
        st.markdown(response_text)

# --- Display chat using styled bubbles ---
for msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
    st.markdown(
        f'<div class="chat-container"><div class="chat-bubble {bubble_class}">{msg["parts"]}</div></div>',
        unsafe_allow_html=True
    )

