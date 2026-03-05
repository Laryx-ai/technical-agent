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

_rag_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a SaaS technical support assistant.\n\n"
     "Use the provided documentation to answer the user question.\n\n"
     "If the answer is not found in the documentation, "
     "say you don't know instead of guessing.\n\n"
     "Documentation:\n{context}"),
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


def get_rag_response(user_message: str, provider: str = "groq", history: list[dict] | None = None) -> str:
    try:
        llm = _providers.get(provider)
        if llm is None:
            return f"Error: Unknown provider '{provider}'."

        vectorstore = _load_vectorstore()
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
            {"context": retriever | format_docs, "input": RunnablePassthrough(), "history": lambda _: _build_history(history or [])}
            | _rag_prompt
            | llm
            | StrOutputParser()
        )
        return chain.invoke(user_message)
    except Exception as e:
        return f"Error: {str(e)}"
