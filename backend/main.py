from fastapi import FastAPI
from pydantic import BaseModel
from services.llm import get_llm_response

app = FastAPI()

class ChatReq(BaseModel):
    prompt: str

class ChatRes(BaseModel):
    response: str

@app.post("/chat", response_model=ChatRes)
def chat(req: ChatReq):
    response_msg = get_llm_response(req.prompt)
    return {"response": response_msg}