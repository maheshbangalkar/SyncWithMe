import streamlit as st
from Common.Config_Loader import config
from Module.SyncWithMeChatBot import SyncWithMeChatBot
from Common.Sheet_Functions import SheetClass as sc
import os
from PIL import Image
from Common import Constant as c
# -------------------------
# Page setup
# -------------------------
current_dir = os.path.dirname(__file__)
img_path = os.path.join(current_dir, "images", "SyncWithMe Logo.png")
css_path = os.path.join(current_dir, "styles", "styles.css")
assistant_path = os.path.join(current_dir, "images", "syncwithme_assistant.png")
user_path = os.path.join(current_dir, "images", "syncwithme_user.png")


st.set_page_config(page_title="SyncWithMe", page_icon=assistant_path)
# -------------------------
# Load external CSS
# -------------------------
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at {file_path}")

load_css(css_path)

# -------------------------
# Top logo + title in a row
# -------------------------
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

# -------------------------
# Initialize chatbot in session state
# -------------------------
if "chatbot" not in st.session_state:
    sheet = sc()
    client = config.get_client()
    gemini_model = config.get_model("GEMINI_2_5_FLASH")
    st.session_state["chatbot"] = SyncWithMeChatBot(client, gemini_model, sheet)

chatbot = st.session_state["chatbot"]

# -------------------------
# Initialize chat messages
# -------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

# -------------------------
# Sidebar Chat History
# -------------------------
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

    # Render user messages
    for i, msg in enumerate(st.session_state["messages"]):
        if msg["role"] == "user":

            preview = msg["content"][:30] + ("..." if len(msg["content"]) > 30 else "")

            # clickable HTML div with hover full text
            if st.markdown(
                f"""
                <div class="history-btn" title="{msg['content']}" 
                     onclick="window.parent.postMessage({{'history_click': {i}}}, '*');">
                    {preview}
                </div>
                """,
                unsafe_allow_html=True
            ):
                pass

# Handle click event
history_click = st.session_state.get("history_click", None)

# -------------------------
# Display all messages
# -------------------------
for msg in st.session_state["messages"]:
    if msg["role"] == "assistant":
        st.chat_message("assistant", avatar=assistant_path).write(msg["content"])
    else:
        st.chat_message("user", avatar=user_path).write(msg["content"])

# -------------------------
# Mode selector + chat input
# -------------------------
# Ensure processing state exists
if "is_processing" not in st.session_state:
    st.session_state["is_processing"] = False

prompt = st.chat_input(
    "Ask anything", 
    disabled=st.session_state["is_processing"])

# -------------------------
# Process new input
# -------------------------
# If user submits a prompt
if prompt and not st.session_state["is_processing"]:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["is_processing"] = True
    st.rerun()


# If processing mode is active, generate response
if st.session_state["is_processing"]:
    user_message = st.session_state["messages"][-1]["content"]

    msg = c.THINKING if thinking_mode else c.GENERATING

    with st.spinner(msg):
        response_text = chatbot.get_gemini_text_response(user_message, thinking_mode)

    # Store assistant message
    st.session_state["messages"].append({
        "role": "assistant",
        "content": response_text
    })

    # Unlock input
    st.session_state["is_processing"] = False
    st.rerun()