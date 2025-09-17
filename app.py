# ----------------------------- CSS & Theme ------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Comfortaa:wght@400;700&display=swap');

/* --- Body background & general --- */
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

/* Sidebar input & select boxes */
[data-testid="stSidebar"] .stSelectbox>div>div>div[role="listbox"],
[data-testid="stSidebar"] .stTextInput>div>div>input,
[data-testid="stSidebar"] .stTextArea>div>div>textarea {
    background-color: #D9FEC9 !important;
    color: #333 !important;
    border: 2px solid #D8C5DD;
    border-radius: 6px;
}

/* --- Top bar --- */
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
    font-size: 80px;
    color: #000; /* black inside for readability */
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

# ----------------------------- Pixel title & star field ------------------------
st.markdown("""
<div class="pixel-title-container">
    <h1 class="pixel-title">Bearfruit</h1>
</div>
<script>
const container = document.querySelector('.pixel-title-container');
for(let i=0;i<80;i++){
    const star = document.createElement('div');
    star.classList.add('star');
    star.style.top = Math.random()*80 + 'px';
    star.style.left = Math.random()*container.offsetWidth + 'px';
    container.appendChild(star);
}
</script>
<p class="subtitle">Your ASU Event Finder Assistant</p>
""", unsafe_allow_html=True)
