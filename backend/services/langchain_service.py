"""
langchain_service.py — Pure LLM chat (no knowledge base)

Handles direct conversations with an LLM using a fixed system prompt.
No documents are retrieved — the model answers entirely from its own
pre-trained knowledge plus the conversation history sent by the client.

Used by:  POST /chat  (provider=groq | mistral)
Providers: Groq (LLaMA 3.3 70B), Mistral AI

Compare with rag_service.py, which retrieves relevant document chunks
before calling the LLM and constrains the answer to those chunks.
"""
import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import SecretStr

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

_providers = {
    "mistral": ChatMistralAI(api_key=SecretStr(os.getenv("MISTRAL_API_KEY") or "")),
    "groq": ChatGroq(model="llama-3.3-70b-versatile", api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")),
}


def _get_chat_prompt() -> ChatPromptTemplate:
    """Build the system prompt dynamically from agent config."""
    # Import here to avoid circular imports at module level
    from .agent_config_service import resolve_system_prompt
    system_text = resolve_system_prompt()
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_text),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )


def _build_history(history: list[dict]) -> list:
    messages = []
    for msg in history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages


def get_langchain_response(user_message: str, provider: str = "mistral", history: list[dict] | None = None) -> str:
    try:
        llm = _providers.get(provider)
        if llm is None:
            return f"Error: Unknown provider '{provider}'. Choose from: {list(_providers.keys())}"
        prompt = _get_chat_prompt()
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"input": user_message, "history": _build_history(history or [])})
    except Exception as e:
        return f"Error: {str(e)}"


# Convenience wrapper
def get_groq_response(user_message: str) -> str:
    return get_langchain_response(user_message, provider="groq")