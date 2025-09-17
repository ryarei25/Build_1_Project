# --- CSS & Theme ---
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
}
.subtitle {
    text-align:center;
    font-family:'Comfortaa', cursive;
    font-size:18px;
    margin-bottom: 20px;
    color: #FFF;  /* subtitle white */
}

/* --- Chat bubbles (unchanged) --- */
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
.chat-container { display: flex; flex-direction: column; }

/* --- Inputs & selectbox --- */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>div[role="listbox"],
select, option {
    background-color: #FFFAF0 !important;  /* match user bubble color */
    border: 2px solid #FFB6C1;
    border-radius: 12px;
    color: #333;
    font-family: 'Comfortaa', cursive;
    padding: 8px;
}

/* --- Selectbox labels --- */
.stSelectbox>label { color: #FFF !important; }

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

