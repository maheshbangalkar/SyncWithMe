import streamlit as st
import sys
import os

# =========================================================
# Setup paths FIRST (so page_icon can use them)
# =========================================================
CURRENT_FILE = os.path.abspath(__file__)
UI_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.dirname(UI_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

current_dir = os.path.dirname(__file__)
img_path = os.path.join(current_dir, "images", "SyncWithMe Logo.png")
css_path = os.path.join(current_dir, "styles", "styles.css")
assistant_path = os.path.join(current_dir, "images", "syncwithme_assistant.png")
user_path = os.path.join(current_dir, "images", "syncwithme_user.png")

# Page setup — To run before Streamlit renders anything
# =========================================================
st.set_page_config(
    page_title="SyncWithMe",
    page_icon=assistant_path if os.path.exists(assistant_path) else None,
)

# =========================================================
# Now safe to import project modules
# =========================================================
from Common.Config_Loader import config
from Module.SyncWithMeChatBot import SyncWithMeChatBot
from Common.Sheet_Functions import SheetClass as sc
from Common import Constant as c
from PIL import Image

# =========================================================
# Load external CSS
# =========================================================
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at {file_path}")

load_css(css_path)

# =========================================================
# Header (logo + title)
# =========================================================
col1, col2 = st.columns([1, 4])

with col1:
    if os.path.exists(img_path):
        img = Image.open(img_path)
        img = img.resize((120, 120))
        st.image(img)
    else:
        st.warning(f"Image not found at {img_path}")

with col2:
    st.title("SyncWithMe ChatBot 🔄🤖")
    st.caption("Your personal assistant to sync with the world 🌏 — powered by Gemini 💠")

# =========================================================
# Initialize chatbot and sheet handler
# =========================================================
if "chatbot" not in st.session_state:
    try:
        sheet = sc()  # auto detects Streamlit or local
    except Exception as e:
        st.error(f"Google Sheet error: {e}")
        sheet = None

    client = config.get_client()
    model_name = config.get_model("GEMINI_2_5_FLASH")

    st.session_state["chatbot"] = SyncWithMeChatBot(
        client=client,
        model=model_name,
        sheet=sheet
    )

chatbot = st.session_state["chatbot"]

# =========================================================
# Initialize chat messages
# =========================================================
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

# =========================================================
# Sidebar History
# =========================================================
with st.sidebar:
    options = {"Thinking Mode": True, "Normal Mode": False}
    thinking_mode_label = st.radio(
        "Select Mode:",
        options=list(options.keys()),
        index=1
    )
    thinking_mode = options[thinking_mode_label]

    st.markdown("---")
    st.header("Chat History 🕒")

    for i, msg in enumerate(st.session_state["messages"]):
        if msg["role"] == "user":
            preview = msg["content"][:30] + ("..." if len(msg["content"]) > 30 else "")
            st.markdown(
                f"""
                <div class="history-btn" title="{msg['content']}" 
                     onclick="window.parent.postMessage({{'history_click': {i}}}, '*');">
                    {preview}
                </div>
                """,
                unsafe_allow_html=True
            )

# =========================================================
# Display chat messages
# =========================================================
for msg in st.session_state["messages"]:
    avatar = assistant_path if msg["role"] == "assistant" else user_path
    avatar = avatar if os.path.exists(avatar) else None

    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

# =========================================================
# Chat Input
# =========================================================
if "is_processing" not in st.session_state:
    st.session_state["is_processing"] = False

prompt = st.chat_input(
    "Ask anything…",
    disabled=st.session_state["is_processing"]
)

# =========================================================
# Handle user prompt
# =========================================================
if prompt and not st.session_state["is_processing"]:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["is_processing"] = True
    st.rerun()

# =========================================================
# Generate assistant response
# =========================================================
if st.session_state["is_processing"]:
    user_message = st.session_state["messages"][-1]["content"]
    spinner_text = c.THINKING if thinking_mode else c.GENERATING

    with st.spinner(spinner_text):
        try:
            response_text = chatbot.get_gemini_text_response(
                user_message,
                thinking_mode
            )
        except Exception as e:
            response_text = f"Error: {str(e)}"

    st.session_state["messages"].append({
        "role": "assistant",
        "content": response_text
    })

    st.session_state["is_processing"] = False
    st.rerun()
