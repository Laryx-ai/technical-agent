"""
agent_config_service.py — Per-Client Agent Configuration

Allows each SaaS client to customise the support agent's persona, system
prompt, and knowledge base path without touching source code.

Config is stored in  backend/agent_config.json  and exposes:
  - agent_name       : display name shown to users (e.g. "Alex")
  - company_name     : SaaS product name ("CloudDesk")
  - system_prompt    : full system prompt override (optional)
  - llm_provider     : default LLM provider ("groq" | "mistral")
  - welcome_message  : greeting shown when the chat first loads

Endpoints (wired in main.py):
  GET  /agent/config          → read current config
  POST /agent/config          → update config (partial or full)
  POST /agent/config/reset    → restore factory defaults
"""
from __future__ import annotations

import json
import os
from typing import Any

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../agent_config.json")

_DEFAULTS: dict[str, Any] = {
    "agent_name": "Alex",
    "company_name": "CloudDesk",
    'system_prompt': (
        "You are {agent_name}, a friendly and helpful support agent for {company_name}. "

    "Speak naturally like a human — relaxed, clear, and slightly informal. "
    "Avoid sounding like documentation or marketing content. "

    "Guidelines:\n"
    "- Use short sentences and natural phrasing\n"
    "- Occasionally use soft fillers like 'basically', 'just', 'you can'\n"
    "- Acknowledge user intent or frustration when relevant\n"
    "- Personalize responses if the user shares context\n"
    "- Do NOT overwhelm with too many features or details\n"
    "- End with a helpful follow-up when appropriate\n"

    "Stay focused on helping the user solve their problem."
),
    "llm_provider": "groq",
    "welcome_message": (
        "Hi there! I'm {agent_name}, your {company_name} support assistant. "
        "How can I help you today?"
    ),
    "rag_top_k": 4,
    "max_history_turns": 10,
}


def _load() -> dict[str, Any]:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                stored = json.load(f)
            # Merge with defaults so new keys always exist
            merged = {**_DEFAULTS, **stored}
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def _save(config: dict[str, Any]) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_config() -> dict[str, Any]:
    """Return the current agent configuration."""
    return _load()


def update_config(updates: dict[str, Any]) -> dict[str, Any]:
    """
    Apply *updates* on top of the existing config and persist.
    Only keys present in the defaults schema are accepted.
    """
    config = _load()
    for key, value in updates.items():
        if key in _DEFAULTS:
            config[key] = value
    _save(config)
    return config


def reset_config() -> dict[str, Any]:
    """Restore factory defaults and persist."""
    _save(dict(_DEFAULTS))
    return dict(_DEFAULTS)


def resolve_system_prompt(config: dict[str, Any] | None = None) -> str:
    """
    Return the system prompt with {agent_name} and {company_name} resolved.
    """
    cfg = config or _load()
    return cfg["system_prompt"].format(
        agent_name=cfg["agent_name"],
        company_name=cfg["company_name"],
    )


def resolve_welcome_message(config: dict[str, Any] | None = None) -> str:
    cfg = config or _load()
    return cfg["welcome_message"].format(
        agent_name=cfg["agent_name"],
        company_name=cfg["company_name"],
    )
