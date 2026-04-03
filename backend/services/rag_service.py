"""
rag_service.py — Retrieval-Augmented Generation (knowledge base chat)

Before calling the LLM, this service retrieves the top-k most relevant
chunks from the local FAISS vector index (built from knowledge_base/).
Those chunks are injected into the prompt as documentation context.
The LLM is instructed to answer only from that context and say
"I don't know" when the answer isn't there.

Intent-aware: the detected intent is injected as an extra instruction so
the LLM can adjust its tone (e.g. technical for API, empathetic for billing).

Used by:  POST /rag  (provider=groq | mistral)
          POST /rag/rebuild  — rebuilds the FAISS index from disk

Key difference from langchain_service.py:
  langchain_service  → open-ended chat, no document grounding
  rag_service        → answers grounded in knowledge_base/ documents only
"""
import os
import json
import hashlib
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from .langchain_service import _providers, _build_history
from .intent_service import classify_intent, get_intent_context
from .agent_config_service import get_config, resolve_system_prompt

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

_KB_PATH = os.path.join(os.path.dirname(__file__), "../knowledge_base")
_FAISS_PATH = os.path.join(os.path.dirname(__file__), "../faiss_index")
_FAISS_META_PATH = os.path.join(_FAISS_PATH, "meta.json")

# Local embeddings — lazy initialized on first use
_embeddings = None
_vectorstore = None


def _kb_file_paths() -> list[str]:
    paths: list[str] = []
    for root, _, files in os.walk(_KB_PATH):
        for name in files:
            lower = name.lower()
            if lower.endswith(".md") or lower.endswith(".txt") or lower.endswith(".pdf"):
                paths.append(os.path.join(root, name))
    paths.sort()
    return paths


def _kb_signature() -> str:
    """
    Stable signature of KB content state (paths + mtimes + file sizes).
    Used to detect when the FAISS index is stale.
    """
    hasher = hashlib.sha256()
    for path in _kb_file_paths():
        stat = os.stat(path)
        rel_path = os.path.relpath(path, _KB_PATH).replace("\\", "/")
        hasher.update(rel_path.encode("utf-8"))
        hasher.update(str(stat.st_mtime_ns).encode("utf-8"))
        hasher.update(str(stat.st_size).encode("utf-8"))
    return hasher.hexdigest()


def _read_index_meta() -> dict:
    if not os.path.exists(_FAISS_META_PATH):
        return {}
    try:
        with open(_FAISS_META_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_index_meta(signature: str, vectors: int) -> None:
    os.makedirs(_FAISS_PATH, exist_ok=True)
    payload = {"kb_signature": signature, "vectors": vectors}
    with open(_FAISS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _get_embeddings() -> MistralAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = MistralAIEmbeddings(
            model="mistral-embed-2312",
            timeout=300,
            max_retries=3,
            wait_time=10
        )
    return _embeddings


def _build_rag_prompt(intent_context: str = "") -> ChatPromptTemplate:
    """Build a RAG prompt that incorporates the dynamic system prompt from agent config."""
    cfg = get_config()
    agent_name = cfg["agent_name"]
    company_name = cfg["company_name"]
    base_system = (
    f"You are {agent_name}, a support agent for {company_name}.\n\n"

    "CRITICAL RULES:\n"
    "1. Answer using ONLY the provided documentation below.\n"
    "2. If the documentation doesn't contain the answer, say you don't have that information in our docs.\n"
    "3. NEVER make up pricing, features, or any information not in the documentation.\n"
    "4. For short responses like 'yes', 'no', 'ok', 'thanks' - check the conversation history to understand context.\n"
    "5. When a user says 'yes', 'no', or similar brief responses, refer to the previous conversation to understand what they're confirming.\n\n"

    "Response style rules:\n"
    "- Talk like a real human support agent, not like documentation\n"
    "- Keep responses short and natural (3–6 sentences unless needed)\n"
    "- Do NOT list everything — only give what is relevant\n"
    "- Avoid repeating the product name unnecessarily\n"
    "- Avoid marketing phrases\n"
    "- Prefer simple explanations over formal wording\n"
    "- If helpful, ask a follow-up question\n"
)
    if intent_context:
        base_system += f"\nContext hint: {intent_context}\n"
    base_system += "\nDocumentation:\n{context}"

    return ChatPromptTemplate.from_messages([
        ("system", base_system),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])


def _load_vectorstore() -> FAISS:
    """Load existing FAISS index or build one from the knowledge_base folder."""
    global _vectorstore
    kb_sig = _kb_signature()
    meta = _read_index_meta()
    index_matches_kb = (
        os.path.exists(_FAISS_PATH)
        and meta.get("kb_signature") == kb_sig
    )

    if _vectorstore is not None:
        if index_matches_kb:
            return _vectorstore
        # KB changed since last in-memory load; rebuild below.
        _vectorstore = None

    if index_matches_kb:
        _vectorstore = FAISS.load_local(_FAISS_PATH, _get_embeddings(), allow_dangerous_deserialization=True)
        return _vectorstore

    _vectorstore = _build_vectorstore()
    return _vectorstore


def _build_vectorstore() -> FAISS:
    """Load .txt/.md/.pdf files from knowledge_base, chunk and embed them."""
    docs = []
    for glob in ["**/*.txt", "**/*.md"]:
        loader = DirectoryLoader(_KB_PATH, glob=glob, loader_cls=TextLoader, silent_errors=True)
        docs.extend(loader.load())
    pdf_loader = DirectoryLoader(_KB_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader, silent_errors=True)
    docs.extend(pdf_loader.load())
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    vectorstore = FAISS.from_documents(chunks, _get_embeddings())
    vectorstore.save_local(_FAISS_PATH)
    _write_index_meta(_kb_signature(), vectorstore.index.ntotal)
    return vectorstore


def rebuild_index() -> str:
    """Force rebuild the FAISS index from current knowledge_base contents."""
    global _vectorstore
    import shutil
    _vectorstore = None
    if os.path.exists(_FAISS_PATH):
        shutil.rmtree(_FAISS_PATH)
    vs = _build_vectorstore()
    _vectorstore = vs
    return f"Index rebuilt with {vs.index.ntotal} vectors."


def get_rag_response(
    user_message: str,
    provider: str = "groq",
    history: list[dict] | None = None,
) -> str:
    try:
        llm = _providers.get(provider)
        if llm is None:
            return f"Error: Unknown provider '{provider}'."

        # Detect intent and get context hint for the prompt
        intent_result = classify_intent(user_message)
        intent_ctx = get_intent_context(intent_result.intent)

        # Use agent-config-aware top_k
        cfg = get_config()
        top_k = int(cfg.get("rag_top_k", 4))

        vectorstore = _load_vectorstore()
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_prompt = _build_rag_prompt(intent_context=intent_ctx)

        chain = (
            {
                "context": retriever | format_docs,
                "input": RunnablePassthrough(),
                "history": lambda _: _build_history(history or []),
            }
            | rag_prompt
            | llm
            | StrOutputParser()
        )
        return chain.invoke(user_message)
    except Exception as e:
        return f"Error: {str(e)}"
