from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatReq(BaseModel):
    prompt: str

class ChatRes(BaseModel):
    response: str

@app.post("/chat", response_model=ChatRes)
def chat(req: ChatReq):
    user_msg = req.prompt
    response_msg = f"backend received: {user_msg}"
    return {'response':response_msg}