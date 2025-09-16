# BearFruit
# Copyright (c) 2025 Arya Reiland
# "This code uses portions of code developed by Prof. Ronald A. Beghetto for a course taught at Arizona State University."

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
# -----------------------------------------------------------------------------


# ----------------------------- Page config -----------------------------------
st.set_page_config(
    page_title="BearFruit",
    layout="centered",
    initial_sidebar_state="expanded",
)
# -----------------------------------------------------------------------------


# ----------------------------- Header image ----------------------------------
try:
    st.image(
        Image.open("Bot.png"),
        caption="Bot Created by Arya Reiland (2025)",
        use_container_width=True,
    )
except Exception as e:
    st.error(f"Error loading image: {e}")

st.markdown(
    "<h1 style='text-align: center;'>Bearfruit, Your ASU Event Finder Assistant</h1>",
    unsafe_allow_html=True,
)
# -----------------------------------------------------------------------------


# ----------------------------- Helpers ---------------------------------------
def load_developer_prompt() -> str:
    """Load system instructions from identity.txt if present; fallback to a default."""
    try:
        with open("identity.txt", encoding="utf-8-sig") as f:
            return f.read()
    except FileNotFoundError:
        st.warning("⚠️ 'identity.txt' not found. Using default prompt.")
        return (
            "You are a helpful assistant. "
            "Be friendly, engaging, and provide clear, concise responses."
        )


def human_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"
# -----------------------------------------------------------------------------


# ----------------------------- Gemini config ---------------------------------
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    system_instructions = load_developer_prompt()

    # Optional Google Search tool
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
# -----------------------------------------------------------------------------


# ----------------------------- App state -------------------------------------
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("uploaded_files", [])
st.session_state.setdefault("user_personality", None)
#new code to keep track of quiz stage and progress
st.session_state.setdefault("quiz_stage", "none")       # 'none'|'offered'|'in_progress'|'completed'
st.session_state.setdefault("quiz_progress", 0)         # index of current quiz step
# -----------------------------------------------------------------------------


# ----------------------------- Sidebar ---------------------------------------
with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown("### About
Briefly describe your bot here for users.")

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
            help="Response Per Day Limits: Pro = 100, Flash = 250, Flash-lite = 1000)",
        )
        st.caption(f"Selected: **{selected_model}**")

        if "chat" not in st.session_state:
            st.session_state.chat = client.chats.create(
                model=selected_model, config=generation_cfg
            )
        elif getattr(st.session_state.chat, "model", None) != selected_model:
            st.session_state.chat = client.chats.create(
                model=selected_model, config=generation_cfg
            )

    # Clear chat
    if st.button("🧹 Clear chat", use_container_width=True, help="Reset chat context"):
        st.session_state.chat_history.clear()
        st.session_state.chat = client.chats.create(
            model=selected_model, config=generation_cfg
        )
        st.toast("Chat cleared.")
        st.rerun()

    # ---- File Upload (Files API) ----
    with st.expander(":material/attach_file: Files (PDF/TXT/DOCX)", expanded=True):
        st.caption(
            "Attach up to **5** files. They’ll be uploaded once and reused across turns. "
            "Files are stored temporarily (~48 hours) in Google’s File store and count toward "
            "your 20 GB storage cap until deleted (✖) or expired."
        )
        uploads = st.file_uploader(
            "Upload files",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        def _upload_to_gemini(u):
            mime = u.type or (mimetypes.guess_type(u.name)[0] or "application/octet-stream")
            data = u.getvalue()
            gfile = client.files.upload(
                file=io.BytesIO(data),
                config=types.UploadFileConfig(mime_type=mime),
            )
            return {
                "name": u.name,
                "size": len(data),
                "mime": mime,
                "file": gfile,
            }

        if uploads:
            slots_left = max(0, 5 - len(st.session_state.uploaded_files))
            newly_added = []
            for u in uploads[:slots_left]:
                already = any(
                    (u.name == f["name"] and u.size == f["size"])
                    for f in st.session_state.uploaded_files
                )
                if already:
                    continue
                try:
                    meta = _upload_to_gemini(u)
                    st.session_state.uploaded_files.append(meta)
                    newly_added.append(meta["name"])
                except Exception as e:
                    st.error(f"File upload failed for **{u.name}**: {e}")
            if newly_added:
                st.toast(f"Uploaded: {', '.join(newly_added)}")

        st.markdown("**Attached files**")
        if st.session_state.uploaded_files:
            for idx, meta in enumerate(st.session_state.uploaded_files):
                left, right = st.columns([0.88, 0.12])
                with left:
                    st.write(
                        f"• {meta['name']}"
                        f"<small> {human_size(meta['size'])} · {meta['mime']}</small>",
                        unsafe_allow_html=True,
                    )
                with right:
                    if st.button("✖", key=f"remove_{idx}", help="Remove this file"):
                        try:
                            client.files.delete(name=meta["file"].name)
                        except Exception:
                            pass
                        st.session_state.uploaded_files.pop(idx)
                        st.rerun()
            st.caption(f"{5 - len(st.session_state.uploaded_files)} slots remaining.")
        else:
            st.caption("No files attached.")

    # Show & delete server-stored files (developer)
    with st.expander("🛠️ Developer: See and Delete all files stored on Google server", expanded=False):
        try:
            files_list = client.files.list()
            if not files_list:
                st.caption("No active files on server.")
            else:
                for f in files_list:
                    exp = getattr(f, "expiration_time", None) or "?"
                    size = getattr(f, "size_bytes", None)
                    size_str = f"{size/1024:.1f} KB" if size else "?"
                    st.write(f"• **{f.name}** ({f.mime_type}, {size_str})  Expires: {exp}")
                if st.button("🗑️ Delete all files", use_container_width=True):
                    failed = []
                    for f in files_list:
                        try:
                            client.files.delete(name=f.name)
                        except Exception:
                            failed.append(f.name)
                    if failed:
                        st.error(f"Failed to delete: {', '.join(failed)}")
                    else:
                        st.success("All files deleted from server.")
                        st.rerun()
        except Exception as e:
            st.error(f"Could not fetch files list: {e}")
# -----------------------------------------------------------------------------


# ----------------------------- Chat replay container -------------------------
with st.container():
    for msg in st.session_state.chat_history:
        avatar = "👤" if msg["role"] == "user" else ":material/robot_2:"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["parts"])
# -----------------------------------------------------------------------------


# ----------------------------- Files API helper ------------------------------
def _ensure_files_active(files, max_wait_s: float = 12.0):
    """Poll the Files API for PROCESSING files until ACTIVE or timeout."""
    deadline = time.time() + max_wait_s
    any_processing = True
    while any_processing and time.time() < deadline:
        any_processing = False
        for i, meta in enumerate(files):
            fobj = meta["file"]
            if getattr(fobj, "state", "") not in ("ACTIVE",):
                any_processing = True
                try:
                    updated = client.files.get(name=fobj.name)
                    files[i]["file"] = updated
                except Exception:
                    pass
        if any_processing:
            time.sleep(0.6)
# -----------------------------------------------------------------------------


# ----------------------------- ASU Event fetch/filter ------------------------
ICS_URL = "https://sundevilcentral.eoss.asu.edu/ics?from_date=15+Sep+2025&to_date=31+Dec+2025&school=arizonau"


def parse_ics(ics_text: str):
    events = []
    current_event = {}
    for line in ics_text.splitlines():
        if line.startswith("BEGIN:VEVENT"):
            current_event = {}
        elif line.startswith("END:VEVENT"):
            if "SUMMARY" in current_event and "DTSTART" in current_event:
                events.append(
                    {
                        "title": current_event.get("SUMMARY", "No title"),
                        "start": current_event.get("DTSTART"),
                        "end": current_event.get("DTEND"),
                        "location": current_event.get("LOCATION", "No location specified"),
                    }
                )
        elif line.startswith("SUMMARY:"):
            current_event["SUMMARY"] = line[len("SUMMARY:") :].strip()
        elif line.startswith("DTSTART"):
            dt_str = line.split(":", 1)[1].strip()
            try:
                current_event["DTSTART"] = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
            except Exception:
                current_event["DTSTART"] = datetime.strptime(dt_str, "%Y%m%d")
        elif line.startswith("DTEND"):
            dt_str = line.split(":", 1)[1].strip()
            try:
                current_event["DTEND"] = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
            except Exception:
                current_event["DTEND"] = datetime.strptime(dt_str, "%Y%m%d")
        elif line.startswith("LOCATION:"):
            current_event["LOCATION"] = line[len("LOCATION:") :].strip()
    return events


def fetch_asu_events():
    try:
        r = requests.get(ICS_URL)
        r.raise_for_status()
        return parse_ics(r.text)
    except Exception as ex:
        st.error(f"Failed to fetch ASU events: {ex}")
        return []


if "asu_events" not in st.session_state:
    st.session_state.asu_events = fetch_asu_events()

filter_keyword = st.text_input("Filter events by keyword (leave blank for all):").lower()
if filter_keyword:
    filtered_events = [
        e
        for e in st.session_state.asu_events
        if filter_keyword in e["title"].lower()
    ]
else:
    filtered_events = st.session_state.asu_events

st.session_state.filtered_events_for_ai = filtered_events

if filtered_events:
    event_texts = []
    for e in filtered_events[:10]:
        start_str = e["start"].strftime("%a, %b %d %I:%M %p")
        end_str = e["end"].strftime("%I:%M %p") if e["end"] else "N/A"
        location = e["location"] or "No location specified"
        event_texts.append(f"- {e['title']} ({start_str} – {end_str}) at {location}")
    events_summary = "Upcoming ASU events matching your preferences:
" + "
".join(event_texts)
else:
    events_summary = "No events match your filter."
# -----------------------------------------------------------------------------


# ----------------------------- Load personalities JSON -----------------------
JSON_PATH = Path(__file__).with_name("16personalities.json")
personalities: list = []
try:
    if JSON_PATH.exists():
        personalities = json.loads(JSON_PATH.read_text(encoding="utf-8-sig"))
        st.success(f"Loaded {len(personalities)} personality entries!")
    else:
        st.warning("⚠️ '16personalities.json' not found; continuing without personality data.")
except json.JSONDecodeError as e:
    st.error(f"Invalid JSON in {JSON_PATH.name}: {e}. Continuing without personality data.")
    personalities = []
except Exception as e:
    st.error(f"Unexpected error loading {JSON_PATH.name}: {e}. Continuing without personality data.")
    personalities = []
# -----------------------------------------------------------------------------


# ----------------------------- Personality helper ----------------------------
def get_personality_text():
    if st.session_state.get("user_personality"):
        return f"User personality: {st.session_state['user_personality']}"
    elif st.session_state.uploaded_files:
        return "User uploaded a personality PDF; infer personality type from it."
    else:
        return "User personality unknown" # changed cause code handles offering quiz

# New code for handling user resposne to quiz offer
def user_said_yes(text: str) -> bool:
    t = text.strip().lower()
    return any(p in t for p in ("yes", "yep", "yeah", "sure", "ok", "okay", "let's do it", "sounds good"))

def user_said_no(text: str) -> bool:
    t = text.strip().lower()
    return any(p in t for p in ("no", "nope", "not now", "skip", "maybe later"))

def seems_like_preference(text: str) -> bool:
    t = text.strip().lower()
    #  heuristic: a single keyword like "book", "music", "art", etc. counts as a preference
    keywords = ("book", "music", "art", "movie", "film", "concert", "sports", "game",
                "coding", "tech", "volunteer", "career", "network", "dance", "outdoor",
                "hiking", "writing", "poetry", "club", "workshop")
    return any(k in t for k in keywords)
# -----------------------------------------------------------------------------


# ----------------------------- Chat input / send -----------------------------
if user_prompt := st.chat_input("Message your bot…"):
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    personality_text = get_personality_text()

    # ---- Aware of xonversation state to stop re-offering the quiz ----
    if user_said_yes(user_prompt) and st.session_state.quiz_stage in ("none", "offered"):
        st.session_state.quiz_stage = "in_progress"
        st.session_state.quiz_progress = max(st.session_state.quiz_progress, 0)
    elif user_said_no(user_prompt) and st.session_state.quiz_stage in ("none", "offered"):
        st.session_state.quiz_stage = "completed"  # don't ask again
    elif seems_like_preference(user_prompt):
        st.session_state.quiz_stage = "completed"  # treat concrete prefs as enough; skip quiz
    elif st.session_state.quiz_stage == "none":
        st.session_state.quiz_stage = "offered"    # first contact with unknown prefs

    # Filter events based on user input + next week
    filter_keyword = user_prompt.lower()
    now = datetime.now()
    one_week = now + timedelta(days=7)
    filtered_events = [
        e
        for e in st.session_state.asu_events
        if (filter_keyword in e["title"].lower() or filter_keyword in e.get("location", "").lower())
        and now <= e["start"] <= one_week
    ]
    if filtered_events:
        event_texts = []
        for e in filtered_events[:10]:
            start_str = e["start"].strftime("%a, %b %d %I:%M %p")
            end_str = e.get("end").strftime("%I:%M %p") if e.get("end") else "N/A"
            location = e.get("location", "No location specified")
            event_texts.append(f"- {e['title']} ({start_str} – {end_str}) at {location}")
        events_summary = (
            "Here are upcoming events based on your preferences and next week timing:
"
            + "
".join(event_texts)
        )
    else:
        events_summary = "No events match your criteria for the next week."

    #Additional Code changes to keep track of stage o qus
    state_directive = f"""
APP_STATE:
- quiz_stage: {st.session_state.quiz_stage}
- quiz_progress: {st.session_state.quiz_progress}

GUIDANCE FOR ASSISTANT (follow strictly):
- If quiz_stage == 'offered' and the user accepted (e.g., said yes), start Quiz Question 1 now. Do NOT re-offer the quiz.
- If quiz_stage == 'in_progress', ask exactly one next quiz question. Do NOT re-offer the quiz.
- If quiz_stage == 'completed', never re-offer the quiz; use known preferences/answers to recommend events/clubs.
- If the user provides clear preferences at any time, skip/stop the quiz and recommend events/clubs accordingly.
"""

    user_prompt_with_events = f"""

User message: {user_prompt}

Personality context: {personality_text}

Personality database: {json.dumps(personalities)}

Upcoming events (next week): {events_summary}

{state_directive}
Instructions:
1. Recommend events that best match the user's preferences and personality.
2. If the user's personality is unknown **and** quiz_stage == 'none', invite a short quiz; otherwise follow APP_STATE above (do not re-offer).
3. Be friendly and concise.
"""

    with st.chat_message("assistant", avatar=":material/robot_2:"):
        try:
            contents_to_send = [types.Part(text=user_prompt_with_events)]
            if st.session_state.uploaded_files:
                _ensure_files_active(st.session_state.uploaded_files)
                for meta in st.session_state.uploaded_files:
                    contents_to_send.append(meta["file"])  # pass file handles

            response = st.session_state.chat.send_message(contents_to_send)
            full_response = response.text if hasattr(response, "text") else str(response)

            st.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "parts": full_response})

        except Exception as e:
            st.error(f"❌ Error from Gemini: {e}")
# -----------------------------------------------------------------------------

