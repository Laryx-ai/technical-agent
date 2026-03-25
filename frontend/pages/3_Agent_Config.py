import streamlit as st
from utils import api, sidebar_agent_info

st.set_page_config(
    page_title="Settings — SaaS Support Agent",
    layout="wide",
)

sidebar_agent_info()

st.title("Settings")
st.caption("Configure model behaviour and agent identity. Changes take effect immediately.")

# Load current agent config
config_data, config_err = api("get", "/agent/config")
if config_err:
    st.error(config_err)
    st.stop()

cfg = config_data or {}

# Model Settings (live, no save needed)
st.subheader("Model Settings")
ms_col1, ms_col2 = st.columns(2)
_service = ms_col1.selectbox(
    "Service",
    ["rag", "chat"],
    index=0 if st.session_state.get("_service", "rag") == "rag" else 1,
    key="_service",
    help="RAG uses the knowledge base. Chat uses the LLM directly.",
)
_provider_options = ["groq", "mistral"] if _service == "rag" else ["groq", "mistral", "hf"]
_saved = st.session_state.get("_provider", "groq")
_provider_idx = _provider_options.index(_saved) if _saved in _provider_options else 0
ms_col2.selectbox(
    "Provider",
    _provider_options,
    index=_provider_idx,
    key="_provider",
)
st.caption(f"Chat page will use: `{st.session_state['_service']} / {st.session_state['_provider']}`")

st.divider()

# Agent Configuration
st.subheader("Agent Configuration")
st.caption("Customise the agent's identity and LLM behaviour for your SaaS product.")

with st.form("agent_config_form"):
    st.markdown("**Identity**")
    col_a, col_b = st.columns(2)
    agent_name = col_a.text_input("Agent Name", value=cfg.get("agent_name", "Alex"))
    company_name = col_b.text_input("Company / Product Name", value=cfg.get("company_name", "CloudDesk"))
    welcome_msg = st.text_input(
        "Welcome Message",
        value=cfg.get("welcome_message", ""),
        help="Use {agent_name} and {company_name} as placeholders.",
    )

    st.markdown("**LLM Behaviour**")
    system_prompt = st.text_area(
        "System Prompt",
        value=cfg.get("system_prompt", ""),
        height=270,
        help="Use {agent_name} and {company_name} as placeholders.",
    )
    col_c, col_d = st.columns(2)
    llm_provider = col_c.selectbox(
        "Default LLM Provider",
        ["groq", "mistral"],
        index=0 if cfg.get("llm_provider", "groq") == "groq" else 1,
    )
    rag_top_k = col_d.number_input(
        "RAG Top-K (retrieved chunks)",
        min_value=1, max_value=10,
        value=int(cfg.get("rag_top_k", 4)),
        help="Number of knowledge base chunks to retrieve for RAG responses. Higher may improve accuracy but increase latency and cost.",
    )
    max_history = st.number_input(
        "Max conversation history turns",
        min_value=1, max_value=50,
        value=int(cfg.get("max_history_turns", 10)),
        help="Number of recent conversation turns to keep in context. Higher may improve response quality but increase latency and cost.",
    )

    save_col, reset_col = st.columns([3, 1])
    submitted = save_col.form_submit_button("Save Configuration", type="primary", use_container_width=True)
    reset_clicked = reset_col.form_submit_button("Reset to Defaults", use_container_width=True)

if submitted:
    updates = {
        "agent_name": agent_name,
        "company_name": company_name,
        "welcome_message": welcome_msg,
        "system_prompt": system_prompt,
        "llm_provider": llm_provider,
        "rag_top_k": rag_top_k,
        "max_history_turns": max_history,
    }
    _, save_err = api("post", "/agent/config", json=updates)
    if save_err:
        st.error(save_err)
    else:
        st.success("Configuration saved. The agent will use the new settings on the next message.")
        st.session_state.pop("welcome_msg", None)
        st.rerun()

if reset_clicked:
    _, reset_err = api("post", "/agent/config/reset")
    if reset_err:
        st.error(reset_err)
    else:
        st.success("Configuration reset to factory defaults.")
        st.session_state.pop("welcome_msg", None)
        st.rerun()

