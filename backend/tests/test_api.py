"""
Integration-style tests for all FastAPI endpoints in main.py.

All LLM / RAG / KB service calls are mocked so no real API keys or
vector index are needed.  The fixtures in conftest.py provide a shared
app instance; each test patches only the functions it exercises.
"""
import importlib
import json
import os
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from services.intent_service import IntentResult

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

_DUMMY_INTENT = IntentResult(
    intent="general",
    label="General Inquiry",
    confidence=0.5,
    matched_patterns=[],
)

_DUMMY_DOC_META = {
    "filename": "test.md",
    "size_bytes": 42,
    "modified": "2026-01-01T00:00:00Z",
}


# ===========================================================================
# Health
# ===========================================================================

def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "agent" in data
    assert "company" in data
    assert data["version"] == "2.0.0"


# ===========================================================================
# POST /chat
# ===========================================================================

def test_chat_groq_provider(client):
    with patch("main.get_langchain_response", return_value="groq answer"), \
         patch("main.classify_intent", return_value=_DUMMY_INTENT):
        resp = client.post("/chat", json={"prompt": "hello", "provider": "groq"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["response"] == "groq answer"
    assert body["provider"] == "groq"
    assert body["intent"] == "general"
    assert body["intent_label"] == "General Inquiry"


def test_chat_mistral_provider(client):
    with patch("main.get_langchain_response", return_value="mistral answer"), \
         patch("main.classify_intent", return_value=_DUMMY_INTENT):
        resp = client.post("/chat", json={"prompt": "hello", "provider": "mistral"})

    assert resp.status_code == 200
    assert resp.json()["response"] == "mistral answer"


def test_chat_hf_provider(client):
    with patch("main.get_hf_response", return_value="hf answer"), \
         patch("main.classify_intent", return_value=_DUMMY_INTENT):
        resp = client.post("/chat", json={"prompt": "tell me something", "provider": "hf"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["response"] == "hf answer"
    assert body["provider"] == "hf"


def test_chat_unknown_provider_returns_error_message(client):
    resp = client.post("/chat", json={"prompt": "hello", "provider": "unknown_xyz"})
    assert resp.status_code == 200
    assert "Unknown provider" in resp.json()["response"]


def test_chat_passes_history_to_llm(client):
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    with patch("main.get_langchain_response", return_value="ok") as mock_llm, \
         patch("main.classify_intent", return_value=_DUMMY_INTENT):
        resp = client.post(
            "/chat",
            json={"prompt": "how are you?", "provider": "groq", "history": history},
        )

    assert resp.status_code == 200
    mock_llm.assert_called_once()
    _, kwargs = mock_llm.call_args
    assert kwargs.get("history") == history or mock_llm.call_args[0][2] == history


def test_chat_default_provider_is_langchain(client):
    """When no provider specified, defaults to 'groq' (service='langchain')."""
    with patch("main.get_langchain_response", return_value="default") as mock_llm, \
         patch("main.classify_intent", return_value=_DUMMY_INTENT):
        resp = client.post("/chat", json={"prompt": "hi"})
    assert resp.status_code == 200


# ===========================================================================
# POST /rag  and  POST /rag/rebuild
# ===========================================================================

def test_rag_chat_returns_grounded_answer(client):
    with patch("main.get_rag_response", return_value="rag answer"), \
         patch("main.classify_intent", return_value=_DUMMY_INTENT):
        resp = client.post("/rag", json={"prompt": "what is the billing cycle?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["response"] == "rag answer"
    assert body["service"] == "rag"
    assert "intent" in body


def test_rag_rebuild_triggers_rebuild(client):
    with patch("main.rebuild_index", return_value="Index rebuilt with 5 vectors.") as mock_rebuild:
        resp = client.post("/rag/rebuild")

    assert resp.status_code == 200
    assert "message" in resp.json()
    mock_rebuild.assert_called_once()


# ===========================================================================
# POST /intent
# ===========================================================================

def test_detect_intent_returns_classification(client):
    billing_intent = IntentResult(
        intent="billing",
        label="Billing & Subscription",
        confidence=0.8,
        matched_patterns=[r"\bbill\b"],
    )
    with patch("main.classify_intent", return_value=billing_intent):
        resp = client.post("/intent", json={"text": "I have a billing question"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "billing"
    assert body["label"] == "Billing & Subscription"
    assert body["confidence"] == 0.8


def test_detect_intent_general_fallback(client):
    with patch("main.classify_intent", return_value=_DUMMY_INTENT):
        resp = client.post("/intent", json={"text": "just a random query"})

    assert resp.status_code == 200
    assert resp.json()["intent"] == "general"


# ===========================================================================
# POST /feedback
# ===========================================================================

def test_submit_feedback_records_event(client):
    target = os.path.join("backend", "logs", "test_feedback.jsonl")
    if os.path.exists(target):
        os.remove(target)
    payload = {
        "message_id": "msg-1",
        "rating": "up",
        "prompt": "How do I reset password?",
        "response": "Use the reset link.",
        "provider": "groq",
        "service": "rag",
        "intent_label": "Account & Login",
    }
    with patch("main._FEEDBACK_FILE", target):
        resp = client.post("/feedback", json=payload)

    assert resp.status_code == 200
    assert os.path.exists(target)
    with open(target, "r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["message_id"] == "msg-1"
    assert row["rating"] == "up"
    os.remove(target)


def test_submit_feedback_rejects_invalid_rating(client):
    resp = client.post("/feedback", json={"message_id": "msg-1", "rating": "meh"})
    assert resp.status_code == 422


# ===========================================================================
# Agent Config
# ===========================================================================

def test_get_agent_config_returns_all_fields(client):
    resp = client.get("/agent/config")
    assert resp.status_code == 200
    data = resp.json()
    for field in ("agent_name", "company_name", "llm_provider", "rag_top_k"):
        assert field in data


def test_update_agent_config_partial_update(client):
    resp = client.post("/agent/config", json={"agent_name": "TestBot"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["config"]["agent_name"] == "TestBot"
    # Restore
    client.post("/agent/config/reset")


def test_update_agent_config_empty_payload_is_rejected(client):
    resp = client.post("/agent/config", json={})
    assert resp.status_code == 400


def test_update_agent_config_unknown_fields_are_ignored(client):
    """Only known keys are accepted; unknown keys should be silently dropped."""
    resp = client.post("/agent/config", json={"agent_name": "TempBot", "unknown_field": "x"})
    assert resp.status_code == 200
    # Restore
    client.post("/agent/config/reset")


def test_reset_agent_config_restores_defaults(client):
    client.post("/agent/config", json={"agent_name": "Temp"})
    resp = client.post("/agent/config/reset")
    assert resp.status_code == 200
    assert resp.json()["config"]["agent_name"] == "Alex"
    assert resp.json()["config"]["company_name"] == "CloudDesk"


def test_get_welcome_message(client):
    resp = client.get("/agent/welcome")
    assert resp.status_code == 200
    msg = resp.json()["message"]
    assert isinstance(msg, str)
    assert len(msg) > 0


# ===========================================================================
# Knowledge Base
# ===========================================================================

def test_list_kb_documents(client):
    with patch("main.list_documents", return_value=[_DUMMY_DOC_META]):
        resp = client.get("/kb/documents")

    assert resp.status_code == 200
    docs = resp.json()["documents"]
    assert isinstance(docs, list)
    assert docs[0]["filename"] == "test.md"


def test_read_kb_document_success(client):
    with patch("main.get_document", return_value="# Hello\nworld"):
        resp = client.get("/kb/documents/faq.md")

    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "faq.md"
    assert body["content"] == "# Hello\nworld"


def test_read_kb_document_not_found_returns_404(client):
    with patch("main.get_document", side_effect=FileNotFoundError("not found")):
        resp = client.get("/kb/documents/missing.md")
    assert resp.status_code == 404


def test_read_kb_document_bad_filename_returns_400(client):
    with patch("main.get_document", side_effect=ValueError("bad filename")):
        resp = client.get("/kb/documents/bad..file")
    assert resp.status_code == 400


def test_upload_kb_document_json(client):
    with patch("main.save_document", return_value=_DUMMY_DOC_META):
        resp = client.post(
            "/kb/documents",
            json={"filename": "new.md", "content": "# New doc"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "document" in body
    assert body["document"]["filename"] == "test.md"


def test_upload_kb_document_invalid_extension_returns_400(client):
    with patch("main.save_document", side_effect=ValueError("Extension '.exe' is not allowed")):
        resp = client.post(
            "/kb/documents",
            json={"filename": "evil.exe", "content": "bad content"},
        )
    assert resp.status_code == 400


def test_upload_kb_file_pdf_success(client):
    with patch("main.save_document", return_value=_DUMMY_DOC_META) as mock_save:
        resp = client.post(
            "/kb/documents/upload-file",
            files={"file": ("guide.pdf", b"%PDF-1.4 test", "application/pdf")},
        )

    assert resp.status_code == 200
    mock_save.assert_called_once_with("guide.pdf", b"%PDF-1.4 test")


def test_upload_kb_file_rejects_disallowed_extension(client):
    resp = client.post(
        "/kb/documents/upload-file",
        files={"file": ("malware.exe", b"binary", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert ".pdf" in resp.json()["detail"]


def test_delete_kb_document_success(client):
    with patch("main.delete_document", return_value="faq.md"):
        resp = client.delete("/kb/documents/faq.md")

    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"]


def test_delete_kb_document_not_found_returns_404(client):
    with patch("main.delete_document", side_effect=FileNotFoundError("not found")):
        resp = client.delete("/kb/documents/ghost.md")
    assert resp.status_code == 404


def test_delete_kb_document_bad_filename_returns_400(client):
    with patch("main.delete_document", side_effect=ValueError("bad filename")):
        resp = client.delete("/kb/documents/bad..file")
    assert resp.status_code == 400


# ===========================================================================
# API-key authentication
# ===========================================================================

def test_api_key_blocks_request_when_configured(monkeypatch):
    """When API_KEY env var is set, a request without the header gets 403."""
    monkeypatch.setenv("API_KEY", "supersecret")
    import main as m
    importlib.reload(m)
    c = TestClient(m.app)
    assert c.get("/health").status_code == 403


def test_api_key_accepts_valid_header(monkeypatch):
    """A request with the correct X-Client-Key header passes auth."""
    monkeypatch.setenv("API_KEY", "supersecret")
    import main as m
    importlib.reload(m)
    c = TestClient(m.app)
    assert c.get("/health", headers={"X-Client-Key": "supersecret"}).status_code == 200


def test_api_key_not_required_when_unset(monkeypatch):
    """When API_KEY is empty or unset, all requests are allowed through."""
    monkeypatch.delenv("API_KEY", raising=False)
    import main as m
    importlib.reload(m)
    c = TestClient(m.app)
    assert c.get("/health").status_code == 200
