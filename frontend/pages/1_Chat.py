import streamlit as st
import uuid
from utils import api, sidebar_agent_info

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

if "_max_history_turns" not in st.session_state:
    cfg, _ = api("get", "/agent/config")
    st.session_state._max_history_turns = int((cfg or {}).get("max_history_turns", 10))

if "history" not in st.session_state:
    st.session_state.history = []

if "pending" not in st.session_state:
    st.session_state.pending = None

if "prefill" not in st.session_state:
    st.session_state.prefill = ""

if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = {}

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


def _trim_history(messages: list[dict], max_turns: int) -> list[dict]:
    """Keep only the most recent turns to bound token usage and response latency."""
    keep_messages = max(max_turns, 1) * 2
    return messages[-keep_messages:]

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
    for idx, msg in enumerate(st.session_state.history):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("intent_label"):
                st.caption(f"{msg['intent_label']}  ·  via `{service}/{provider}`")
            if msg["role"] == "assistant":
                message_id = msg.get("id") or f"msg_{idx}"
                rating = st.session_state.feedback_submitted.get(message_id)
                if rating:
                    st.caption("Thanks for your feedback.")
                else:
                    _, c1, _sp, c2 = st.columns([6, 1, 0.0001, 1])
                    up_clicked = c1.button("👍", key=f"fb_up_{message_id}")
                    down_clicked = c2.button("👎", key=f"fb_down_{message_id}")
                    if up_clicked or down_clicked:
                        fb_rating = "up" if up_clicked else "down"
                        payload = {
                            "message_id": message_id,
                            "rating": fb_rating,
                            "prompt": msg.get("prompt"),
                            "response": msg.get("content"),
                            "provider": msg.get("provider", provider),
                            "service": msg.get("service", service),
                            "intent_label": msg.get("intent_label"),
                        }
                        _, fb_err = api("post", "/feedback", json=payload)
                        if fb_err:
                            st.warning(f"Could not submit feedback: {fb_err}")
                        else:
                            st.session_state.feedback_submitted[message_id] = fb_rating
                            st.rerun()

    if st.session_state.pending:
        pending_prompt = st.session_state.pending
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                max_turns = int(st.session_state.get("_max_history_turns", 10))
                payload = {
                    "prompt": pending_prompt,
                    "provider": provider,
                    "history": _trim_history(st.session_state.history[:-1], max_turns),
                }
                endpoint = "/rag" if service == "rag" else "/chat"
                resp_data, err = api("post", endpoint, json=payload)
        if err:
            response = f"{err}"
            i_label = None
        else:
            data = resp_data or {}
            response = data.get("response", "")
            i_label = data.get("intent_label")
        st.session_state.history.append({
            "role": "assistant",
            "id": str(uuid.uuid4()),
            "content": response,
            "prompt": pending_prompt,
            "provider": provider,
            "service": service,
            "intent_label": i_label,
        })
        st.session_state.pending = None
        st.rerun()

    if st.button("Clear", key="clear_chat"):
        st.session_state.history = []
        st.session_state.feedback_submitted = {}
        st.session_state.prefill = ""
        st.session_state.pending = None
        st.rerun()

_busy = bool(st.session_state.pending)
submitted_input = st.chat_input(
    "Waiting for response…" if _busy else "Ask a support question…",
    key="chat_input_bottom",
    disabled=_busy,
)
if submitted_input and not _busy and submitted_input.strip():
    _queue(submitted_input.strip())
