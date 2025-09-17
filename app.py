st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Comfortaa:wght@400;700&display=swap');

/* --- Background & general body --- */
body {
    font-family: 'Comfortaa', cursive;
    background: linear-gradient(135deg, #C6D7E6, #FFCDEB);
    color: #333;
    overflow-x: hidden;
}

/* --- Sidebar --- */
[data-testid="stSidebar"] {
    background-color: #D8C5DD !important;
    color: #333;
    border-right: 2px solid #C6D7E6;
}

/* --- Top bar (menu) --- */
header {
    background-color: #FFCDEB !important;
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
        6px 6px #CCE7FF;
    display: inline-block;
    z-index: 2;
}

/* --- Pixel stars --- */
.star {
    position: absolute;
    width: 2px;
    height: 2px;
    background-color: #FFE4A4; /* soft yellow */
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
    box-shadow: 2px 2px 0 #CCE7FF;
}

.user-bubble {
    background-color: #D9FEC9;  /* soft green */
    border-color: #CCE7FF;
    color: #333;
    align-self: flex-end;
}

.bot-bubble {
    background-color: #D9FEC9;  /* soft green */
    border-color: #CCE7FF;
    color: #333;
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
    border: 2px solid #CCE7FF;
    border-radius: 6px;
    color: #333;
    font-family: 'Comfortaa', cursive;
    padding: 6px;
}

/* --- Buttons --- */
.stButton>button {
    background-color: #D9FEC9 !important;
    color: #333 !important;
    border: 2px solid #CCE7FF !important;
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
