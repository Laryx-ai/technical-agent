from fastapi import FastAPI
from pydantic import BaseModel
from services import get_hf_response, get_langchain_response, get_rag_response, rebuild_index

app = FastAPI()

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


@app.post("/chat", response_model=ChatRes)
def chat(req: ChatReq):
    if req.provider == "hf":
        response_msg = get_hf_response(req.prompt)
    elif req.provider in ("groq", "mistral"):
        response_msg = get_langchain_response(req.prompt, provider=req.provider, history=req.history)
    else:
        response_msg = f"Unknown provider '{req.provider}'. Choose from: groq, mistral, hf"
    return {
        "response": response_msg,
        "service": "chat",
        "provider": req.provider,
    }


@app.post("/rag", response_model=ChatRes)
def rag_chat(req: RagReq):
    response_msg = get_rag_response(req.prompt, provider=req.provider, history=req.history)
    return {"response": response_msg, "service": "rag", "provider": req.provider}


@app.post("/rag/rebuild")
def rag_rebuild():
    result = rebuild_index()
    return {"message": result}