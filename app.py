# BearFruit
# Copyright (c) 2025 Arya Reiland

import io
import time
import json
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image
import streamlit as st

# Optional date parsing
try:
    import dateparser
except ImportError:
    dateparser = None
    st.warning("⚠️ 'dateparser' not installed. Natural language date filters will be limited.")

# ----------------------------- Page Config -----------------------------------
st.set_page_config(
    page_title="Bearfruit",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ----------------------------- CSS Theme -------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap');

/* Main app background */
.css-1d391kg {  /* Main content container */
    background: #C6D7E6;
    color: #333;
}

/* Sidebar background */
.css-1d391kg + div section[aria-label="Sidebar"] {
    background-color: #E5DBFF !important;
    color: #333 !important;
}

/* Header image container safe */
.stImage {
    margin-bottom: 10px;
}

/* Pixel title with stars */
.pixel-title-container {
    position: relative;
    text-align: center;
    margin-bottom: 10px;
}

.pixel-title {
    display: inline-block;
    font-family: 'Comfortaa', cursive;
    font-size: 80px;
    color: #000;
    text-shadow:
        2px 2px #000,
        4px 4px #FFCDEB,
        6px 6px #000;
    letter-spacing: 2px;
}

.star {
    position: absolute;
    font-size: 20px;
    color: #FFE4A4;
    animation: twinkle 2s infinite;
}

@keyframes twinkle {
    0%,100% {opacity:0.2;}
    50% {opacity:1;}
}

/* Chat bubbles */
.chat-bubble {
    max-width: 70%;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 10px;
    font-family: 'Comfortaa', cursive;
    font-size: 14px;
    box-shadow: 0 0 10px rgba(0,0,0,0.2);
}

.user-bubble {
    background-color: #D9FEC9; 
    border: 2px solid #CCE7FF;
    align-self: flex-end;
    color: #333;
}

.bot-bubble {
    background-color: #FFE4A4; 
    border: 2px solid #FFCDEB;
    align-self: flex-start;
    color: #333;
}

/* Buttons */
.stButton>button {
    background-color: #D9FEC9 !important;
    color: #333 !important;
    border: 2px solid #FFCDEB !important;
    border-radius: 8px !important;
    font-size: 14px;
    padding: 8px 16px;
    transition: all 0.2s ease-in-out;
}

.stButton>button:hover {
    background-color: #CCE7FF !important;
    transform: scale(1.05);
}

/* Inputs and selectboxes */
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div>div {
    background-color: #D9FEC9 !important;
    border: 2px solid #CCE7FF !important;
    border-radius: 6px;
    color: #333;
    font-family: 'Comfortaa', cursive;
    padding: 6px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------- Header ----------------------------------------
try:
    st.image(
        Image.open("Bot.png"),
        caption="Bot Created by Arya Reiland (2025)",
        use_container_width=True,
    )
except Exception as e:
    st.error(f"Error loading image: {e}")

# Pixel title with static stars
st.markdown("""
<div class="pixel-title-container">
  <div class="pixel-title">Bearfruit</div>
  <div class="star" style="top: -10px; left: 30px;">✨</div>
  <div class="star" style="top: 0px; left: 150px;">✨</div>
  <div class="star" style="top: 20px; left: 300px;">✨</div>
  <div class="star" style="top: -15px; left: 250px;">✨</div>
  <div class="star" style="top: 10px; left: 400px;">✨</div>
</div>
<p style="text-align:center; font-family:'Comfortaa', cursive;">Your ASU Event Finder Assistant</p>
""", unsafe_allow_html=True)

st.caption("Please be patient, sometimes I take extra time to think.")

# ----------------------------- Sidebar ---------------------------------------
with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown("### About: Briefly describe your bot here for users.")
    # Add model selection, clear chat, etc., here
    st.selectbox("Choose a model:", ["gemini-2.5-pro","gemini-2.5-flash","gemini-2.5-flash-lite"])
    st.button("🧹 Clear chat")

# ----------------------------- Chat Container ---------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_prompt = st.chat_input("Message your bot…")
if user_prompt:
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})

for msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if msg["role"]=="user" else "bot-bubble"
    st.markdown(f'<div class="chat-bubble {bubble_class}">{msg["parts"]}</div>', unsafe_allow_html=True)

