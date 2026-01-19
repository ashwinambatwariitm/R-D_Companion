import streamlit as st
import requests
import json
import os

import time
from storage import load_chats, save_chats, new_chat


OLLAMA_URL = "http://localhost:11434/api/generate"
CHAT_FILE = "chat_history.json"

# ---------------- Page config ----------------
st.set_page_config(
    page_title="R&D Companion",
    layout="wide"
)

# ---------- Initialize chats -----------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "active_chat" not in st.session_state:
    chat = new_chat()
    st.session_state.chats.insert(0, chat)
    st.session_state.active_chat = chat["chat_id"]
    save_chats(st.session_state.chats)

# Adding a stop button flag
if "stop_generation" not in st.session_state:
    st.session_state.stop_generation = False

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "qwen2.5:3b"

MODEL_CONFIG = {
    "qwen2.5:3b": {
        "temperature": 0.2,
        "num_predict": 120,
        "num_ctx": 2048   
    },
    "llama3.2:3b": {
        "temperature": 0.2,
        "num_predict": 150,
        "num_ctx": 2048
    },
    "llama3:8b": {
        "temperature": 0.3,
        "num_predict": 200,
        "num_ctx": 4096
    },
    "deepseek-r1:7b": {
        "temperature": 0.1,
        "num_predict": 200,
        "num_ctx": 4096
    }
}

# ---------------- Ollama call ----------------
def ollama_generate(prompt, model):
    config = MODEL_CONFIG.get(model, {})
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "temperature": config.get("temperature", 0.2),
        "num_predict": config.get("num_predict", 120),
        "num_ctx": config.get("num_ctx", 2048)
    }
    r = requests.post(OLLAMA_URL, json=payload)
    r.raise_for_status()
    
    # Ollama may returns multiple json objects (newline seperated)
    lines = r.text.strip().splitlines()
    
    response_text = ""
    for line in lines:
        try:
            data = json.loads(line)
            response_text += data.get("response", "")
        except json.JSONDecodeError:
            continue
    
    return response_text

import re

# ---------------- LaTeX fix ----------------
def fix_latex(text: str) -> str:
    """
    Convert common LaTeX math to Streamlit-friendly format
    """
    # Wrap f(x)=... style equations
    text = re.sub(
        r"(f\(x\)\s*=\s*[^.\n]+)",
        r"$$\1$$",
        text
    )

    # Wrap \begin{cases} ... \end{cases}
    text = re.sub(
        r"(\\begin\{cases\}.*?\\end\{cases\})",
        r"$$\1$$",
        text,
        flags=re.DOTALL
    )

    return text

# ====================================================
# 🔒 FIXED HEADER (MUST BE BEFORE CHAT RENDERING)
# ====================================================
display_name = st.session_state.selected_model.split(":")[0]

st.markdown(
    f"""
    <div style="
        background: linear-gradient(90deg, #ff6a00, #ffd500, #4cd137, #00a8ff);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 30px;
        font-weight: bold;
    ">
        🤖 R&D Companion <br>
        <span style="font-size:16px;">
            Local AI Assistant powered by <b>{display_name}</b> (Ollama)
        </span><br>
        <span style="font-size:14px; opacity:0.85;">Developed by Ashwin Ambatwar</span>
    </div>
    """,
    unsafe_allow_html=True
)


# ----------------- Left Sidebar -----------------
st.sidebar.title("🧠 Chats")
st.sidebar.markdown(
    """
    <div style="
        margin-top: -5px;
    ">
    """,
    unsafe_allow_html=True
)

if st.sidebar.button("➕ New chat"):
    chat = new_chat()
    st.session_state.chats.insert(0, chat)
    st.session_state.active_chat = chat["chat_id"]
    st.session_state.force_clear = True
    save_chats(st.session_state.chats)
    st.rerun()

chat_container = st.sidebar.container(height=260)

with chat_container:
    st.markdown(
        """
        <div style="
            max-height: 260px;
            overflow-y: auto;
        ">
        """,
        unsafe_allow_html=True
    )

    for idx, chat in enumerate(st.session_state.chats):
        col1, col2 = st.columns([0.88, 0.12])

        with col1:
            if st.button(
                f"{chat['title']}", #  \n🕒 {chat['created_at']}",
                key=f"chat_{chat['chat_id']}"
            ):
                st.session_state.active_chat = chat["chat_id"]
                st.rerun()

        with col2:
            if st.button("X", key=f"del_{chat['chat_id']}"):
                if len(st.session_state.chats) > 1:
                    st.session_state.chats.pop(idx)
                    if st.session_state.active_chat == chat["chat_id"]:
                        st.session_state.active_chat = st.session_state.chats[0]["chat_id"]
                    save_chats(st.session_state.chats)
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


#  Load active chats
active_chat = next(
    c for c in st.session_state.chats
    if c["chat_id"] == st.session_state.active_chat
)

# 🔥 Ensure brand-new chat is completely empty on right panel
if st.session_state.get("force_clear", False):
    active_chat["messages"] = []
    st.session_state.force_clear = False


# ---------------- Render Messages ------------------------
for msg in active_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg["time"] is not None:
            st.caption(f"⏱ {msg['time']:.2f} seconds")

# 🔥 Clear messages for brand-new chat
if st.session_state.get("force_clear", False):
    active_chat["messages"] = []
    st.session_state.force_clear = False


# ---------------- Sidebar ----------------
st.sidebar.title("🧠 System Status")
st.sidebar.success("Ollama connected")
st.sidebar.info(f"Model: {st.session_state.selected_model}")

st.sidebar.divider()

st.sidebar.title("⚙ Settings")
st.sidebar.selectbox(
    "🧠 Select Model",
    options=[
        "qwen2.5:3b",
        "llama3.2:3b",
        "llama3:8b",
        "deepseek-r1:7b"
    ],
    key="selected_model"
)



st.sidebar.divider()


st.write("")

stop_col = st.columns([0.85, 0.15])

with stop_col[1]:
    if st.button("⏹ Stop"):
        st.session_state.stop_generation = True
        
prompt = st.chat_input(f"Ask me anything (offline, local {display_name})...")


if prompt:
    active_chat["messages"].append({
        "role": "user",
        "content": prompt,
        "time": None
    })

    if active_chat["title"] == "New chat":
        active_chat["title"] = prompt.strip().split("\n")[0][:40]

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            st.session_state.stop_generation = False
            
            start = time.time()
            reply = ollama_generate(prompt, st.session_state.selected_model)
            duration = time.time() - start

            if st.session_state.stop_generation:
                st.warning("Generation stopped by user.")
            else:
                reply = fix_latex(reply)
                st.markdown(reply)
                st.caption(f"⏱ {duration:.2f} seconds")

    if not st.session_state.stop_generation:
        active_chat["messages"].append({
            "role": "assistant",
            "content": reply,
            "time": duration
        })

    save_chats(st.session_state.chats)

