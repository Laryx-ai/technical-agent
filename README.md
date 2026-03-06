# Chat Agent - Basics

A full-stack AI chat application built with **FastAPI** (backend) and **Streamlit** (frontend), supporting multiple LLM providers and a RAG knowledge base via LangChain.

---

## Project Structure

```
python-web/
├── .env                              # API keys (not committed)
├── requirements.txt
├── backend/
│   ├── main.py                       # FastAPI app — /chat, /rag, /rag/rebuild
│   ├── faiss_index/                  # Auto-generated FAISS vector index
│   ├── knowledge_base/               # Drop .txt or .md files here for RAG
│   │   ├── DOCUMENTATION.md
│   │   ├── faq.md
│   │   ├── conversations.md
│   │   ├── billing.md
│   │   ├── troubleshooting.md
│   │   ├── integrations.md
│   │   └── changelog.md
│   └── services/
│       ├── __init__.py               # Exports all service functions
│       ├── mistral.py                # Mistral AI via mistralai SDK (Conversations API)
│       ├── hf.py                     # HuggingFace Inference API
│       ├── langchain_service.py      # LangChain LCEL chain — multi-provider + memory
│       └── rag_service.py            # RAG pipeline — FAISS retrieval + LLM answering
└── frontend/
    └── app.py                        # Streamlit chat UI with sidebar service selector
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Streamlit | 1.54.0 |
| Backend | FastAPI | 0.129.0 |
| Backend | Uvicorn | 0.41.0 |
| LLM Orchestration | LangChain (LCEL) | 1.2.10 |
| LLM Orchestration | langchain-core | 1.2.17 |
| LLM Providers | Mistral AI (`langchain-mistralai`) | 1.1.1 |
| LLM Providers | Groq — LLaMA 3.3 70B (`langchain-groq`) | 1.1.2 |
| LLM Providers | HuggingFace (`huggingface_hub`) | 1.4.1 |
| Vector Store | FAISS (`faiss-cpu`) | 1.13.2 |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers | 5.2.3 |
| Data Validation | Pydantic | 2.12.5 |

> **Python Compatibility:** Use **Python 3.12** (recommended). Python 3.14+ triggers a `UserWarning` from `langchain-core` due to dropped Pydantic V1 compatibility shims (`pydantic.v1`), and other dependencies (`faiss-cpu`, `sentence-transformers`) may not be fully tested on Python 3.14.

---

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> All required packages (including `langchain-mistralai`, `langchain-groq`, `langchain-huggingface`, `langchain-community`, `sentence-transformers`, `faiss-cpu`, etc.) are already pinned in `requirements.txt`.

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_AGENT_ID=your_mistral_agent_id
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
```

| Variable | Used In | Purpose |
|---|---|---|
| `MISTRAL_API_KEY` | `mistral.py`, `langchain_service.py` | Authenticates all requests to Mistral |
| `MISTRAL_AGENT_ID` | `mistral.py` only | Identifies the pre-built Mistral Agent (Conversations API). Not needed for LangChain's chat completions. |
| `GROQ_API_KEY` | `langchain_service.py` | Authenticates requests to Groq (LLaMA 3.3 70B) |
| `HF_TOKEN` | `hf.py` | Authenticates HuggingFace Inference API |

- Get a free Groq key at https://console.groq.com
- Get a Mistral key at https://console.mistral.ai
- Get a Mistral Agent ID at https://console.mistral.ai/agents

---

## Running the App

### Start the backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`  
Interactive API docs: `http://localhost:8000/docs`

### Start the frontend (Streamlit)

```bash
cd frontend
streamlit run app.py
```

Frontend runs at `http://localhost:8501`

---

## API Reference

### `POST /chat`

Chat using a provider of your choice. Routing is **provider-driven** — no `service` field needed.

**Request:**
```json
{
  "prompt": "Your message here",
  "provider": "groq",
  "history": [
    { "role": "user", "content": "Hi" },
    { "role": "assistant", "content": "Hello! How can I help?" }
  ]
}
```

**`provider` options:**

| Provider | Backend | Notes |
|---|---|---|
| `groq` | `langchain_service.py` | LLaMA 3.3 70B via Groq API |
| `mistral` | `langchain_service.py` | Mistral via Mistral API |
| `hf` | `hf.py` | Mistral-7B via HuggingFace Inference API |

**Response:**
```json
{
  "response": "Assistant reply here",
  "service": "chat",
  "provider": "groq"
}
```

---

### `POST /rag`

Answer using the knowledge base (RAG).

**Request:**
```json
{
  "prompt": "What are your pricing plans?",
  "provider": "groq",
  "history": []
}
```

**Response:**
```json
{
  "response": "CloudDesk offers three plans: Starter at $19/month...",
  "service": "rag",
  "provider": "groq"
}
```

---

### `POST /rag/rebuild`

Rebuild the FAISS index after adding new files to `knowledge_base/`.

**No request body required.**

**Response:**
```json
{ "message": "Index rebuilt with 142 vectors." }
```

**How to call:**
```bash
# curl
curl -X POST http://localhost:8000/rag/rebuild

# Python
import requests
requests.post("http://localhost:8000/rag/rebuild")

# Browser — Swagger UI
http://localhost:8000/docs → POST /rag/rebuild → Execute
```

---

## Request Flow

### Layers

```
┌─────────────────────────────────────────────────┐
│                   Browser / User                │
└───────────────────────┬─────────────────────────┘
                        │  HTTP (localhost:8501)
┌───────────────────────▼─────────────────────────┐
│           Frontend  (Streamlit — app.py)        │
│  • Sidebar: chat/rag service + provider picker  │
│  • Maintains chat history in session state      │
│  • Streams assistant reply character-by-char    │
└───────────────────────┬─────────────────────────┘
                        │  POST /chat  or  POST /rag
                        │  JSON body + history array
                        │  HTTP (localhost:8000)
┌───────────────────────▼─────────────────────────┐
│            Backend  (FastAPI — main.py)         │
│  • Validates request with Pydantic models       │
│  • Routes to the correct service function       │
└──────┬──────────────────────────┬───────────────┘
       │  /chat                   │  /rag
┌──────▼───────────┐   ┌──────────▼──────────────┐
│ provider=groq    │   │      rag_service         │
│ provider=mistral │   │ • FAISS vector search    │
│  → langchain_    │   │ • Top-4 chunks retrieved │
│    service.py    │   │ • Chunks injected into   │
│ provider=hf      │   │   prompt as context      │
│  → hf.py         │   └──────────┬───────────────┘
└──────┬───────────┘              │
       │                          │
┌──────▼──────────────────────────▼───────────────┐
│              LLM Provider                       │
│  • Groq  → llama-3.3-70b-versatile (default)   │
│  • Mistral → mistral-latest                     │
│  • HuggingFace → Inference API                  │
└─────────────────────────────────────────────────┘
```

---

### `/chat` request step-by-step

```
User selects service=chat, provider=groq|mistral|hf
    → Streamlit appends message to history
    → POSTs { prompt, provider, history } to /chat
        → FastAPI inspects provider:
            provider=groq or mistral
                → langchain_service.py builds LCEL chain:
                      ChatPromptTemplate (system + history + input)
                      | ChatGroq / ChatMistralAI
                      | StrOutputParser
            provider=hf
                → hf.py calls HuggingFace Inference API
                      (mistralai/Mistral-7B-Instruct-v0.2)
        → Response JSON returned to frontend
    → Streamlit streams reply character-by-character
→ Reply appended to history for next turn
```

---

### `/rag` request step-by-step

```
User types message
    → Streamlit POSTs to /rag
        → FastAPI calls get_rag_response()
            → rag_service loads FAISS index (or builds it)
            → Sentence-transformer embeds the query
                  (all-MiniLM-L6-v2, runs locally)
            → FAISS retrieves top-4 nearest chunks
            → Chunks formatted and injected as {context}
            → LCEL chain:
                  RAG ChatPromptTemplate (system + context + history + input)
                  | ChatGroq / ChatMistralAI
                  | StrOutputParser
            → LLM answers using only retrieved context
        → Response JSON returned to frontend
    → Streamlit streams reply character-by-character
→ Reply appended to history for next turn
```

---

### Document Ingestion Pipeline

```
knowledge_base/
├── billing.md
├── changelog.md
├── conversations.md
├── DOCUMENTATION.md
├── faq.md
├── integrations.md
└── troubleshooting.md
        │
        │  DirectoryLoader  (glob: **/*.txt, **/*.md)
        ▼
┌───────────────────────────────────────────────┐
│              Raw Documents                    │
│  LangChain Document objects with              │
│  page_content + metadata (source path)        │
└───────────────────────┬───────────────────────┘
                        │
                        │  RecursiveCharacterTextSplitter
                        │  chunk_size=500, chunk_overlap=50
                        ▼
┌───────────────────────────────────────────────┐
│                   Chunks                      │
│  ~66 overlapping text chunks                  │
│  preserves sentence/paragraph boundaries      │
└───────────────────────┬───────────────────────┘
                        │
                        │  HuggingFaceEmbeddings
                        │  model: all-MiniLM-L6-v2
                        │  runs locally (no API key)
                        ▼
┌───────────────────────────────────────────────┐
│              384-dim Vectors                  │
│  one dense float vector per chunk             │
└───────────────────────┬───────────────────────┘
                        │
                        │  FAISS.from_documents()
                        ▼
┌───────────────────────────────────────────────┐
│           faiss_index/  (persisted)           │
│  index.faiss  — binary vector index           │
│  index.pkl    — docstore + metadata           │
└───────────────────────────────────────────────┘
```

**Triggered by:** `POST /rag/rebuild` or automatically on first request if no index exists.

**To add new documents:** drop `.txt` or `.md` files into `knowledge_base/`, then call `POST /rag/rebuild`.

---

### `/rag/rebuild` step-by-step

```
POST /rag/rebuild (manual trigger)
    → FastAPI calls rebuild_index()
        → Deletes existing faiss_index/ folder
        → DirectoryLoader reads all .txt + .md files
          from knowledge_base/
        → RecursiveCharacterTextSplitter chunks them
          (500 chars, 50 overlap)
        → HuggingFaceEmbeddings encodes every chunk
        → FAISS index built and saved to faiss_index/
    → Returns { "message": "Index rebuilt with N vectors." }
```

---

## LangChain Setup

### Architecture

LangChain uses LCEL (LangChain Expression Language) to chain components with the `|` operator:

```
ChatPromptTemplate | LLM | StrOutputParser
```

### Multi-provider support

`langchain_service.py` uses a `_providers` dict to switch LLMs with a single flag:

```python
_providers = {
    "mistral": ChatMistralAI(...),
    "groq": ChatGroq(model="llama-3.3-70b-versatile", ...),
}
```

To add a new provider (e.g. Gemini):
```python
from langchain_google_genai import ChatGoogleGenerativeAI
_providers["gemini"] = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=...)
```

### Conversation memory

Chat history is passed as `MessagesPlaceholder` in the prompt. The frontend sends the full history array with each request — no server-side session state needed.

### RAG pipeline

```
User question
    → FAISS retrieves top-4 relevant chunks from knowledge_base/
    → Chunks injected into prompt as context
    → LLM answers using only that context
```

Source files: `.txt` and `.md` files in `knowledge_base/` are automatically loaded, chunked (500 chars, 50 overlap), and embedded using `all-MiniLM-L6-v2`.

---

## Knowledge Base

Add documents to `backend/knowledge_base/` as `.txt` or `.md` files, then rebuild the index:

```bash
# Via API
curl -X POST http://localhost:8000/rag/rebuild

# Or call from browser
http://localhost:8000/docs → POST /rag/rebuild → Execute
```

Current knowledge base covers: account setup, ticket management, billing, troubleshooting, integrations, changelog, and FAQ.

---

## Frontend

The Streamlit UI includes a **sidebar** with:
- **Service selector** — `rag` (default) | `chat`
- **Provider selector**
  - `rag`  → `groq` | `mistral`
  - `chat` → `groq` | `mistral` | `hf`
- **Active label** always shown as `service / provider`

Each assistant reply shows a `via service / provider` caption.

> **Default:** The app opens with **RAG** mode enabled — answers are grounded in the knowledge base documents.

### Enabling simple chat (no knowledge base)

To switch to a direct LLM conversation without RAG, select **chat** from the Service dropdown in the sidebar, then pick a provider. The request goes straight to the LLM with no document retrieval.

---

## Local Model (Optional)

To run inference locally without any API key:

1. Install [Ollama](https://ollama.com/download)
2. Pull a model:
   ```bash
   ollama pull mistral
   ```
3. Add to `_providers` in `langchain_service.py`:
   ```python
   from langchain_ollama import ChatOllama
   _providers["ollama"] = ChatOllama(model="mistral")
   ```

> **GPU:** NVIDIA GeForce RTX 3050 6GB — suitable for running 7B models with Ollama and QLoRA fine-tuning.

---

## Fine-tuning (Planned)

For training on a custom dataset using QLoRA (recommended for 6GB VRAM):

```
Dataset (JSONL) → QLoRA fine-tune (trl + peft) → Merged model → Ollama serve → LangChain
```

Required packages: `transformers`, `peft`, `trl`, `bitsandbytes`, `datasets`