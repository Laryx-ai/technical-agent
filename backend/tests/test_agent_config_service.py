"""
Unit tests for services/agent_config_service.py.

All operations use a temporary config file so the real agent_config.json
is never modified.
"""
import json
import pytest

import services.agent_config_service as cfg_mod


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Point _CONFIG_PATH to a fresh temp file for each test."""
    config_file = tmp_path / "agent_config.json"
    monkeypatch.setattr(cfg_mod, "_CONFIG_PATH", str(config_file))
    return config_file


# ===========================================================================
# get_config
# ===========================================================================

class TestGetConfig:
    def test_returns_defaults_when_no_file_exists(self):
        cfg = cfg_mod.get_config()
        assert cfg["agent_name"] == "Alex"
        assert cfg["company_name"] == "CloudDesk"
        assert cfg["llm_provider"] == "groq"
        assert cfg["rag_top_k"] == 4
        assert cfg["max_history_turns"] == 10

    def test_returns_dict(self):
        assert isinstance(cfg_mod.get_config(), dict)

    def test_merges_with_defaults_for_partial_file(self, isolated_config):
        isolated_config.write_text(json.dumps({"agent_name": "CustomBot"}), encoding="utf-8")
        cfg = cfg_mod.get_config()
        assert cfg["agent_name"] == "CustomBot"
        assert cfg["company_name"] == "CloudDesk"  # from defaults

    def test_ignores_corrupt_json(self, isolated_config):
        isolated_config.write_text("not valid json{{{", encoding="utf-8")
        cfg = cfg_mod.get_config()
        assert cfg["agent_name"] == "Alex"  # falls back to defaults

    def test_all_default_keys_present(self):
        cfg = cfg_mod.get_config()
        for key in ("agent_name", "company_name", "system_prompt", "llm_provider",
                    "welcome_message", "rag_top_k", "max_history_turns"):
            assert key in cfg


# ===========================================================================
# update_config
# ===========================================================================

class TestUpdateConfig:
    def test_updates_agent_name(self):
        result = cfg_mod.update_config({"agent_name": "Nova"})
        assert result["agent_name"] == "Nova"

    def test_persists_update_across_calls(self):
        cfg_mod.update_config({"agent_name": "Nova"})
        assert cfg_mod.get_config()["agent_name"] == "Nova"

    def test_partial_update_preserves_other_fields(self):
        cfg_mod.update_config({"company_name": "AcmeCorp"})
        cfg = cfg_mod.get_config()
        assert cfg["company_name"] == "AcmeCorp"
        assert cfg["agent_name"] == "Alex"  # unchanged default

    def test_ignores_unknown_keys(self):
        cfg_mod.update_config({"unknown_key": "value", "agent_name": "Safe"})
        cfg = cfg_mod.get_config()
        assert cfg["agent_name"] == "Safe"
        assert "unknown_key" not in cfg

    def test_updates_rag_top_k_integer(self):
        result = cfg_mod.update_config({"rag_top_k": 8})
        assert result["rag_top_k"] == 8

    def test_updates_multiple_fields_at_once(self):
        result = cfg_mod.update_config({"agent_name": "Zara", "company_name": "ZaraCorp"})
        assert result["agent_name"] == "Zara"
        assert result["company_name"] == "ZaraCorp"


# ===========================================================================
# reset_config
# ===========================================================================

class TestResetConfig:
    def test_restores_default_agent_name(self):
        cfg_mod.update_config({"agent_name": "Temp"})
        result = cfg_mod.reset_config()
        assert result["agent_name"] == "Alex"

    def test_restores_all_defaults(self):
        cfg_mod.update_config({"agent_name": "X", "company_name": "Y", "rag_top_k": 99})
        cfg_mod.reset_config()
        cfg = cfg_mod.get_config()
        assert cfg["agent_name"] == "Alex"
        assert cfg["company_name"] == "CloudDesk"
        assert cfg["rag_top_k"] == 4

    def test_returns_defaults_dict(self):
        result = cfg_mod.reset_config()
        assert isinstance(result, dict)
        assert result == cfg_mod._DEFAULTS


# ===========================================================================
# resolve_system_prompt
# ===========================================================================

class TestResolveSystemPrompt:
    def test_substitutes_agent_name(self):
        cfg_mod.update_config({"agent_name": "Luna"})
        prompt = cfg_mod.resolve_system_prompt()
        assert "Luna" in prompt

    def test_substitutes_company_name(self):
        cfg_mod.update_config({"company_name": "AcmeInc"})
        prompt = cfg_mod.resolve_system_prompt()
        assert "AcmeInc" in prompt

    def test_returns_string(self):
        assert isinstance(cfg_mod.resolve_system_prompt(), str)

    def test_accepts_explicit_config(self):
        custom = {**cfg_mod._DEFAULTS, "agent_name": "Bolt", "company_name": "BoltCo"}
        prompt = cfg_mod.resolve_system_prompt(config=custom)
        assert "Bolt" in prompt
        assert "BoltCo" in prompt


# ===========================================================================
# resolve_welcome_message
# ===========================================================================

class TestResolveWelcomeMessage:
    def test_contains_agent_name(self):
        cfg_mod.update_config({"agent_name": "Aria"})
        msg = cfg_mod.resolve_welcome_message()
        assert "Aria" in msg

    def test_contains_company_name(self):
        cfg_mod.update_config({"company_name": "Nexus"})
        msg = cfg_mod.resolve_welcome_message()
        assert "Nexus" in msg

    def test_returns_string(self):
        assert isinstance(cfg_mod.resolve_welcome_message(), str)

    def test_accepts_explicit_config(self):
        custom = {**cfg_mod._DEFAULTS, "agent_name": "Rex", "company_name": "RexCorp"}
        msg = cfg_mod.resolve_welcome_message(config=custom)
        assert "Rex" in msg
        assert "RexCorp" in msg
