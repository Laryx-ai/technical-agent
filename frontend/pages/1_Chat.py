import streamlit as st
from utils import api, intent_badge, sidebar_agent_info

st.set_page_config(
    page_title="Chat — SaaS Support Agent",
    layout="wide",
)

# Sidebar
info = sidebar_agent_info()

# Read model settings stored by sidebar_agent_info()
service = st.session_state.get("_service", "rag")
provider = st.session_state.get("_provider", "groq")

# Session state
if "welcome_msg" not in st.session_state:
    data, _ = api("get", "/agent/welcome")
    st.session_state.welcome_msg = data["message"] if data else "Hi! How can I help you today?"

if "history" not in st.session_state:
    st.session_state.history = []

if "pending" not in st.session_state:
    st.session_state.pending = None

if "prefill" not in st.session_state:
    st.session_state.prefill = ""

SUGGESTIONS = [
    "How do I reset my password?",
    "What are your pricing plans?",
    "Why aren't tickets being created from email?",
    "How do I set up the Slack integration?",
]

# Queue handler
def _queue(user_prompt: str):
    st.session_state.history.append({"role": "user", "content": user_prompt})
    st.session_state.pending = user_prompt
    st.session_state.prefill = ""
    st.rerun()

# Welcome screen
agent_name = info.get("agent", "Alex") if info else "Alex"

if not st.session_state.history and not st.session_state.pending:
    st.markdown(
        f"<h3 style='text-align:center;padding-top:2rem'>🤖 {agent_name}</h3>"
        f"<p style='text-align:center;color:#888'>{st.session_state.welcome_msg}</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2 = st.columns(2)
    for i, s in enumerate(SUGGESTIONS):
        col = c1 if i % 2 == 0 else c2
        if col.button(s, key=f"sug_{i}", use_container_width=True):
            _queue(s)

# Active chat
else:
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("intent_label"):
                st.caption(
                    intent_badge(msg.get("intent_emoji", "💬"), msg["intent_label"])
                    + f"  ·  via `{service}/{provider}`"
                )

    if st.session_state.pending:
        pending_prompt = st.session_state.pending
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                payload = {
                    "prompt": pending_prompt,
                    "provider": provider,
                    "history": st.session_state.history[:-1],
                }
                endpoint = "/rag" if service == "rag" else "/chat"
                resp_data, err = api("post", endpoint, json=payload)
        if err:
            response = f"⚠️ {err}"
            i_label = i_emoji = None
        else:
            data = resp_data or {}
            response = data.get("response", "")
            i_label = data.get("intent_label")
            i_emoji = data.get("intent_emoji", "💬")
        st.session_state.history.append({
            "role": "assistant",
            "content": response,
            "intent_label": i_label,
            "intent_emoji": i_emoji,
        })
        st.session_state.pending = None
        st.rerun()

    if st.button("Clear conversation", key="clear_chat"):
        st.session_state.history = []
        st.session_state.prefill = ""
        st.session_state.pending = None
        st.rerun()

# Input bar
st.divider()
_busy = bool(st.session_state.pending)
with st.form("chat_form", clear_on_submit=True):
    col_in, col_btn = st.columns([11, 1])
    user_input = col_in.text_input(
        "Message",
        value=st.session_state.prefill,
        placeholder="Waiting for response…" if _busy else "Ask a support question…",
        label_visibility="collapsed",
        disabled=_busy,
    )
    submitted = col_btn.form_submit_button("➤", type="primary", use_container_width=True, disabled=_busy)
    if submitted and not _busy and user_input.strip():
        _queue(user_input.strip())
