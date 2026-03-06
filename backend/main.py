from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
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


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

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
    intent_emoji: str | None = None


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


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health():
    """Liveness check — returns status and current agent identity."""
    config = get_config()
    return {
        "status": "ok",
        "agent": config["agent_name"],
        "company": config["company_name"],
        "version": "2.0.0",
    }


# ---------------------------------------------------------------------------
# Chat endpoints
# ---------------------------------------------------------------------------

@app.post("/chat", response_model=ChatRes, tags=["Chat"])
def chat(req: ChatReq):
    """Open-ended chat powered by the configured LLM (no KB lookup)."""
    if req.provider == "hf":
        response_msg = get_hf_response(req.prompt)
        intent_result = classify_intent(req.prompt)
        return {
            "response": response_msg,
            "service": "chat",
            "provider": req.provider,
            "intent": intent_result.intent,
            "intent_label": intent_result.label,
            "intent_emoji": intent_result.emoji,
        }
    elif req.provider in ("groq", "mistral"):
        response_msg = get_langchain_response(req.prompt, provider=req.provider, history=req.history)
    else:
        response_msg = f"Unknown provider '{req.provider}'. Choose from: groq, mistral, hf"
        return {"response": response_msg, "service": "chat", "provider": req.provider}

    intent_result = classify_intent(req.prompt)
    return {
        "response": response_msg,
        "service": "chat",
        "provider": req.provider,
        "intent": intent_result.intent,
        "intent_label": intent_result.label,
        "intent_emoji": intent_result.emoji,
    }


@app.post("/rag", response_model=ChatRes, tags=["Chat"])
def rag_chat(req: RagReq):
    """Knowledge base-grounded chat using RAG + intent-aware prompting."""
    intent_result = classify_intent(req.prompt)
    response_msg = get_rag_response(req.prompt, provider=req.provider, history=req.history)
    return {
        "response": response_msg,
        "service": "rag",
        "provider": req.provider,
        "intent": intent_result.intent,
        "intent_label": intent_result.label,
        "intent_emoji": intent_result.emoji,
    }


@app.post("/rag/rebuild", tags=["Chat"])
def rag_rebuild():
    """Rebuild the FAISS vector index from the current knowledge base documents."""
    result = rebuild_index()
    return {"message": result}


# ---------------------------------------------------------------------------
# Intent endpoint
# ---------------------------------------------------------------------------

@app.post("/intent", tags=["Intent"])
def detect_intent(req: IntentReq):
    """Classify the intent of a query without generating an answer."""
    result = classify_intent(req.text)
    return {
        "intent": result.intent,
        "label": result.label,
        "emoji": result.emoji,
        "confidence": result.confidence,
    }


# ---------------------------------------------------------------------------
# Agent configuration endpoints
# ---------------------------------------------------------------------------

@app.get("/agent/config", tags=["Agent Config"])
def get_agent_config():
    """Retrieve the current per-client agent configuration."""
    return get_config()


@app.post("/agent/config", tags=["Agent Config"])
def set_agent_config(updates: AgentConfigUpdate):
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
def reset_agent_config():
    """Restore factory default agent configuration."""
    defaults = reset_config()
    return {"message": "Configuration reset to defaults.", "config": defaults}


@app.get("/agent/welcome", tags=["Agent Config"])
def get_welcome():
    """Return the resolved welcome message (with agent_name and company_name substituted)."""
    return {"message": resolve_welcome_message()}


# ---------------------------------------------------------------------------
# Knowledge base management endpoints
# ---------------------------------------------------------------------------

@app.get("/kb/documents", tags=["Knowledge Base"])
def list_kb_documents():
    """List all documents in the knowledge base with metadata."""
    return {"documents": list_documents()}


@app.get("/kb/documents/{filename}", tags=["Knowledge Base"])
def read_kb_document(filename: str):
    """Return the raw text content of a single knowledge base document."""
    try:
        content = get_document(filename)
        return {"filename": filename, "content": content}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/kb/documents", tags=["Knowledge Base"])
def upload_kb_document(doc: KBDocumentUpload):
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
async def upload_kb_file(file: UploadFile = File(...)):
    """
    Upload a .md or .txt file directly.  Multipart form upload.
    After uploading, call /rag/rebuild to update the vector index.
    """
    allowed = {".md", ".txt"}
    import os as _os
    ext = _os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Only .md and .txt files are allowed.")
    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8")
        meta = save_document(file.filename or "upload.txt", content)
        return {"message": "File uploaded.", "document": meta}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")


@app.delete("/kb/documents/{filename}", tags=["Knowledge Base"])
def remove_kb_document(filename: str):
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
