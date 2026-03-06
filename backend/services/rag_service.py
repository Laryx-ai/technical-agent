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
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
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

# Local embeddings — lazy initialized on first use
_embeddings = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def _build_rag_prompt(intent_context: str = "") -> ChatPromptTemplate:
    """Build a RAG prompt that incorporates the dynamic system prompt from agent config."""
    cfg = get_config()
    agent_name = cfg["agent_name"]
    company_name = cfg["company_name"]
    base_system = (
        f"You are {agent_name}, a friendly and knowledgeable support agent for {company_name}.\n\n"
        "Use the provided documentation to answer the user question accurately and concisely.\n"
        "If the answer is not found in the documentation, say you don't know instead of guessing.\n"
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
    if os.path.exists(_FAISS_PATH):
        return FAISS.load_local(_FAISS_PATH, _get_embeddings(), allow_dangerous_deserialization=True)
    return _build_vectorstore()


def _build_vectorstore() -> FAISS:
    """Load all .txt and .md files from knowledge_base, chunk and embed them."""
    docs = []
    for glob in ["**/*.txt", "**/*.md"]:
        loader = DirectoryLoader(_KB_PATH, glob=glob, loader_cls=TextLoader, silent_errors=True)
        docs.extend(loader.load())
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    vectorstore = FAISS.from_documents(chunks, _get_embeddings())
    vectorstore.save_local(_FAISS_PATH)
    return vectorstore


def rebuild_index() -> str:
    """Force rebuild the FAISS index from current knowledge_base contents."""
    import shutil
    if os.path.exists(_FAISS_PATH):
        shutil.rmtree(_FAISS_PATH)
    vs = _build_vectorstore()
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
