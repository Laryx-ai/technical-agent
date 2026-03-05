# python-web

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

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| LLM Orchestration | LangChain (LCEL) |
| LLM Providers | Mistral AI, Groq (LLaMA 3.3 70B), HuggingFace |
| Vector Store | FAISS (local, no cloud needed) |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers |
| Data Validation | Pydantic |

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
pip install langchain-mistralai langchain-groq langchain-huggingface langchain-community langchain-text-splitters sentence-transformers faiss-cpu
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
MISTRAL_API_KEY=your_mistral_api_key
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
```

- Get a free Groq key at https://console.groq.com
- Get a Mistral key at https://console.mistral.ai

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

Chat using a selected service and provider.

**Request:**
```json
{
  "prompt": "Your message here",
  "service": "langchain",
  "provider": "groq",
  "history": [
    { "role": "user", "content": "Hi" },
    { "role": "assistant", "content": "Hello! How can I help?" }
  ]
}
```

**`service` options:** `langchain` | `mistral` | `hf`  
**`provider` options (langchain only):** `groq` | `mistral`

**Response:**
```json
{
  "response": "Assistant reply here",
  "service": "langchain",
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

**Response:**
```json
{ "message": "Index rebuilt with 142 vectors." }
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
│  • Sidebar: service + provider selector         │
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
│ langchain_service│   │      rag_service         │
│ (LCEL chain)     │   │ • FAISS vector search    │
│                  │   │ • Top-4 chunks retrieved │
│ or hf.py         │   │ • Chunks injected into   │
│ (HuggingFace     │   │   prompt as context      │
│  Inference API)  │   └──────────┬───────────────┘
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
User types message
    → Streamlit appends it to history, POSTs to /chat
        → FastAPI reads service + provider from body
            → langchain_service.py builds LCEL chain:
                  ChatPromptTemplate (system + history + input)
                  | ChatGroq / ChatMistralAI
                  | StrOutputParser
            → LLM API called with full message history
        → Response JSON returned to frontend
    → Streamlit streams reply  character-by-character
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
- **Service selector** — `langchain` | `rag` | `mistral` | `hf`
- **Provider selector** — `groq` | `mistral` (shown when `langchain` or `rag` is selected)
- **Active model label** showing the current selection

Each assistant reply shows a `via service / provider` caption.

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