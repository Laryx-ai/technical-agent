import os
import json
from datetime import datetime, timezone
from services.log_config import logger
from fastapi import FastAPI, HTTPException, UploadFile, File, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import Literal
from services import (
    get_hf_response,
    get_langchain_response,
    get_rag_response,
    rebuild_index,
    classify_intent,
    get_config,
    update_config,
    reset_config,
    resolve_welcome_message,
    list_documents,
    save_document,
    delete_document,
    get_document,
)

app = FastAPI(
    title="SaaS Tech Support Agent API",
    description=(
        "AI-powered technical support agent with RAG, intent recognition, "
        "per-client configuration, and knowledge base management."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional API key authentication
# Set API_KEY in your .env to enable.  Leave blank (or unset) to disable.

_API_KEY_VALUE = os.getenv("API_KEY", "").strip()
_api_key_header = APIKeyHeader(name="X-Client-Key", auto_error=False)
_FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "logs", "feedback.jsonl")


def verify_api_key(key: str | None = Security(_api_key_header)):
    """Dependency — passes if API_KEY is not configured, or if the header matches."""
    if not _API_KEY_VALUE:
        return  # auth disabled
    if key != _API_KEY_VALUE:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Client-Key header.")


def _clip(text: str, limit: int = 260) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    return normalized[:limit] + ("..." if len(normalized) > limit else "")


def _normalize(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())

# Request / Response models

class ChatReq(BaseModel):
    prompt: str
    service: str = "langchain"
    provider: str = "groq"
    history: list[dict] = []


class RagReq(BaseModel):
    prompt: str
    provider: str = "groq"
    history: list[dict] = []


class ChatRes(BaseModel):
    response: str
    service: str
    provider: str | None = None
    intent: str | None = None
    intent_label: str | None = None


class IntentReq(BaseModel):
    text: str


class AgentConfigUpdate(BaseModel):
    agent_name: str | None = None
    company_name: str | None = None
    system_prompt: str | None = None
    llm_provider: str | None = None
    welcome_message: str | None = None
    rag_top_k: int | None = None
    max_history_turns: int | None = None


class KBDocumentUpload(BaseModel):
    filename: str
    content: str


class FeedbackReq(BaseModel):
    message_id: str
    rating: Literal["up", "down"]
    prompt: str | None = None
    response: str | None = None
    provider: str | None = None
    service: str | None = None
    intent_label: str | None = None

# Health

@app.get("/health", tags=["System"])
def health(auth: None = Depends(verify_api_key)):
    """Liveness check — returns status and current agent identity."""
    config = get_config()
    return {
        "status": "ok",
        "agent": config["agent_name"],
        "company": config["company_name"],
        "version": "2.0.0",
    }

# Chat endpoints

@app.post("/chat", response_model=ChatRes, tags=["Chat"])
def chat(req: ChatReq, auth: None = Depends(verify_api_key)):
    """Open-ended chat powered by the configured LLM (no KB lookup)."""
    logger.info(f"/chat endpoint called: provider={req.provider}, prompt={_clip(req.prompt)}")
    if req.provider == "hf":
        response_msg = get_hf_response(req.prompt)
        intent_result = classify_intent(req.prompt)
        logger.info(
            f"/chat response: provider={req.provider}, intent={intent_result.intent}, response={_normalize(response_msg)}"
        )
        return {
            "response": response_msg,
            "service": "chat",
            "provider": req.provider,
            "intent": intent_result.intent,
            "intent_label": intent_result.label,
        }
    elif req.provider in ("groq", "mistral"):
        response_msg = get_langchain_response(req.prompt, provider=req.provider, history=req.history)
    else:
        response_msg = f"Unknown provider '{req.provider}'. Choose from: groq, mistral, hf"
        logger.warning(f"/chat response: provider={req.provider}, response={_normalize(response_msg)}")
        return {"response": response_msg, "service": "chat", "provider": req.provider}

    intent_result = classify_intent(req.prompt)
    if response_msg.startswith("Error:"):
        logger.error(
            f"/chat response: provider={req.provider}, intent={intent_result.intent}, response={_normalize(response_msg)}"
        )
    else:
        logger.info(
            f"/chat response: provider={req.provider}, intent={intent_result.intent}, response={_normalize(response_msg)}"
        )
    return {
        "response": response_msg,
        "service": "chat",
        "provider": req.provider,
        "intent": intent_result.intent,
        "intent_label": intent_result.label,
    }


@app.post("/rag", response_model=ChatRes, tags=["Chat"])
def rag_chat(req: RagReq, auth: None = Depends(verify_api_key)):
    """Knowledge base-grounded chat using RAG + intent-aware prompting."""
    logger.info(f"/rag endpoint called: provider={req.provider}, prompt={_clip(req.prompt)}")
    intent_result = classify_intent(req.prompt)
    response_msg = get_rag_response(req.prompt, provider=req.provider, history=req.history)
    if response_msg.startswith("Error:"):
        logger.error(
            f"/rag response: provider={req.provider}, intent={intent_result.intent}, response={_normalize(response_msg)}"
        )
    else:
        logger.info(
            f"/rag response: provider={req.provider}, intent={intent_result.intent}, response={_normalize(response_msg)}"
        )
    return {
        "response": response_msg,
        "service": "rag",
        "provider": req.provider,
        "intent": intent_result.intent,
        "intent_label": intent_result.label,
    }


@app.post("/rag/rebuild", tags=["Chat"])
def rag_rebuild(auth: None = Depends(verify_api_key)):
    """Rebuild the FAISS vector index from the current knowledge base documents."""
    result = rebuild_index()
    return {"message": result}


# Intent endpoint

@app.post("/intent", tags=["Intent"])
def detect_intent(req: IntentReq, auth: None = Depends(verify_api_key)):
    """Classify the intent of a query without generating an answer."""
    result = classify_intent(req.text)
    return {
        "intent": result.intent,
        "label": result.label,
        "confidence": result.confidence,
    }


@app.post("/feedback", tags=["Feedback"])
def submit_feedback(req: FeedbackReq, auth: None = Depends(verify_api_key)):
    """Store per-response feedback from the chat UI."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_id": req.message_id,
        "rating": req.rating,
        "prompt": req.prompt,
        "response": req.response,
        "provider": req.provider,
        "service": req.service,
        "intent_label": req.intent_label,
    }
    os.makedirs(os.path.dirname(_FEEDBACK_FILE), exist_ok=True)
    with open(_FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    logger.info(
        f"/feedback recorded: message_id={req.message_id}, rating={req.rating}, provider={req.provider}, service={req.service}"
    )
    return {"message": "Feedback recorded."}

# Agent configuration endpoints

@app.get("/agent/config", tags=["Agent Config"])
def get_agent_config(auth: None = Depends(verify_api_key)):
    """Retrieve the current per-client agent configuration."""
    return get_config()


@app.post("/agent/config", tags=["Agent Config"])
def set_agent_config(updates: AgentConfigUpdate, auth: None = Depends(verify_api_key)):
    """
    Update agent configuration fields.  Only supplied fields are changed.
    Allows SaaS clients to customise agent name, company, system prompt, etc.
    """
    payload = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=400, detail="No valid fields provided.")
    updated = update_config(payload)
    return {"message": "Configuration updated.", "config": updated}


@app.post("/agent/config/reset", tags=["Agent Config"])
def reset_agent_config(auth: None = Depends(verify_api_key)):
    """Restore factory default agent configuration."""
    defaults = reset_config()
    return {"message": "Configuration reset to defaults.", "config": defaults}


@app.get("/agent/welcome", tags=["Agent Config"])
def get_welcome(auth: None = Depends(verify_api_key)):
    """Return the resolved welcome message (with agent_name and company_name substituted)."""
    return {"message": resolve_welcome_message()}


# Knowledge base management endpoints

@app.get("/kb/documents", tags=["Knowledge Base"])
def list_kb_documents(auth: None = Depends(verify_api_key)):
    """List all documents in the knowledge base with metadata."""
    return {"documents": list_documents()}


@app.get("/kb/documents/{filename}", tags=["Knowledge Base"])
def read_kb_document(filename: str, auth: None = Depends(verify_api_key)):
    """Return the raw text content of a single knowledge base document."""
    try:
        content = get_document(filename)
        return {"filename": filename, "content": content}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/kb/documents", tags=["Knowledge Base"])
def upload_kb_document(doc: KBDocumentUpload, auth: None = Depends(verify_api_key)):
    """
    Upload a new document (or overwrite an existing one) in the knowledge base.
    Accepts plain text or Markdown.  After uploading, call /rag/rebuild to
    update the vector index.
    """
    try:
        meta = save_document(doc.filename, doc.content)
        return {"message": "Document saved.", "document": meta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/kb/documents/upload-file", tags=["Knowledge Base"])
async def upload_kb_file(file: UploadFile = File(...), auth: None = Depends(verify_api_key)):
    """
    Upload a .md, .txt, or .pdf file directly.  Multipart form upload.
    After uploading, call /rag/rebuild to update the vector index.
    """
    allowed = {".md", ".txt", ".pdf"}
    import os as _os
    ext = _os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Only .md, .txt, and .pdf files are allowed.")
    try:
        content_bytes = await file.read()
        meta = save_document(file.filename or "upload.txt", content_bytes)
        return {"message": "File uploaded.", "document": meta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/kb/documents/{filename}", tags=["Knowledge Base"])
def remove_kb_document(filename: str, auth: None = Depends(verify_api_key)):
    """
    Delete a document from the knowledge base.
    Call /rag/rebuild afterwards to update the vector index.
    """
    try:
        removed = delete_document(filename)
        return {"message": f"Document '{removed}' deleted."}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
