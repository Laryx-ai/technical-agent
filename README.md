# SaaS Tech Support Agent

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.129.0-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.54.0-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.2.10-1C3C3C?logo=langchain&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?logo=groq&logoColor=white)
![Mistral AI](https://img.shields.io/badge/Mistral_AI-latest-FF7000?logo=mistral&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-1.4.1-FFD21E?logo=huggingface&logoColor=black)
![FAISS](https://img.shields.io/badge/FAISS-1.13.2-0467DF?logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)

An AI-powered SaaS technical support agent with **RAG-grounded answers**, **intent recognition**, **per-client customisation**, and **knowledge base management** — built with FastAPI + Streamlit and ready for cloud deployment.

---

## Features

| Feature | Description |
|---|---|
| **RAG Chat** | Answers grounded in your product's knowledge base via FAISS vector search |
| **Intent Recognition** | Automatically classifies queries (billing, troubleshooting, account, API, integrations…) |
| **Agent Configuration** | Customise agent name, company, system prompt, and LLM settings per client |
| **Knowledge Base Manager** | Upload, view, and delete `.md`/`.txt` documents via the UI or REST API |
| **Multi-Provider LLM** | Groq (LLaMA 3.3 70B), Mistral AI, HuggingFace Inference API |
| **Conversation Memory** | Full multi-turn history passed to every LLM call |
| **Multi-Page UI** | `st.navigation()` router with Chat, Knowledge Base, Settings, and Docs pages |
| **Two-Step Chat Render** | User message appears instantly; agent response streams in with a spinner — no full-page reload |
| **Live Sidebar Status** | Backend online/offline indicator and KB document count visible on every page |
| **Docker Deployment** | Single `docker-compose up` for local or cloud deployment |

---

## Project Structure

```
technical-agent/
├── .env                              # API keys (not committed — copy from .env.example)
├── .env.example                      # Template for required environment variables
├── requirements.txt
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── backend/
│   ├── main.py                       # FastAPI app — all REST endpoints
│   ├── agent_config.json             # Auto-created per-client config (gitignored)
│   ├── faiss_index/                  # Auto-generated FAISS vector index
│   ├── knowledge_base/               # Drop .txt or .md files here for RAG
│   │   ├── DOCUMENTATION.md
│   │   ├── faq.md
│   │   ├── billing.md
│   │   ├── troubleshooting.md
│   │   ├── integrations.md
│   │   └── changelog.md
│   └── services/
│       ├── __init__.py               # Exports all service functions
│       ├── mistral.py                # Mistral AI via mistralai SDK
│       ├── hf.py                     # HuggingFace Inference API
│       ├── langchain_service.py      # LangChain LCEL chain — multi-provider + memory
│       ├── rag_service.py            # RAG pipeline — FAISS retrieval + intent-aware prompting
│       ├── intent_service.py         # Query intent classification (keyword + heuristic)
│       ├── agent_config_service.py   # Per-client agent configuration management
│       └── kb_service.py             # Knowledge base document CRUD
│   └── tests/
│       ├── conftest.py               # Shared FastAPI TestClient fixture
│       ├── test_api.py               # Endpoint integration tests (all routes)
│       ├── test_intent_service.py    # Intent classifier unit tests
│       ├── test_kb_service.py        # KB service unit tests
│       └── test_agent_config_service.py  # Agent config unit tests
└── frontend/
    ├── app.py                        # st.navigation() router — entry point
    ├── utils.py                      # Shared helpers: api(), intent_badge(), sidebar_agent_info()
    └── pages/
        ├── 1_Chat.py                 # Two-state chat UI (welcome screen / chat history)
        ├── 2_Knowledge_Base.py       # Upload, view, delete documents; rebuild FAISS index
        ├── 3_Agent_Config.py         # Model Settings + Agent Configuration (unified Settings page)
        └── 4_Docs.py                 # Built-in documentation
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Streamlit | 1.54.0 |
| Backend | FastAPI | 0.129.0 |
| Backend | Uvicorn | 0.41.0 |
| LLM Orchestration | LangChain (LCEL) | 1.2.10 |
| LLM Providers | Mistral AI (`langchain-mistralai`) | 1.1.1 |
| LLM Providers | Groq — LLaMA 3.3 70B (`langchain-groq`) | 1.1.2 |
| LLM Providers | HuggingFace (`huggingface_hub`) | 1.4.1 |
| Vector Store | FAISS (`faiss-cpu`) | 1.13.2 |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers | 5.2.3 |
| Intent Recognition | Custom keyword + heuristic classifier | built-in |
| Data Validation | Pydantic | 2.12.5 |
| Containerisation | Docker + docker-compose | — |

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

### 3. Configure environment variables

```bash
cp .env.example .env
# Fill in your API keys in .env
```

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Groq LLaMA 3.3 70B (get free key at console.groq.com) |
| `MISTRAL_API_KEY` | Mistral AI chat + embeddings |
| `MISTRAL_AGENT_ID` | Mistral Agent (optional — only for the Conversations API path) |
| `HF_TOKEN` | HuggingFace Inference API |
| `BACKEND_URL` | Frontend → backend URL (default: `http://localhost:8000`) |

---

## Running Locally

### Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload
```

Runs at `http://localhost:8000`  
Interactive API docs: `http://localhost:8000/docs`

### Frontend (Streamlit)

```bash
cd frontend
streamlit run app.py
```

Runs at `http://localhost:8501`

---

## Docker Deployment

### Local / Cloud

```bash
# Build and start both services
docker-compose up --build

# Detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

- Backend exposed on **port 8000**
- Frontend exposed on **port 8501**
- FAISS index, knowledge base, and agent config are mounted as volumes so data persists across container restarts.

---

## API Reference

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check + agent identity |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Open-ended LLM chat (groq / mistral / hf) |
| `POST` | `/rag` | Knowledge base-grounded chat with intent detection |
| `POST` | `/rag/rebuild` | Rebuild FAISS index from knowledge_base/ |

### Intent

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/intent` | Classify query intent without generating an answer |

### Agent Configuration

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/agent/config` | Read current agent configuration |
| `POST` | `/agent/config` | Update configuration fields |
| `POST` | `/agent/config/reset` | Restore factory defaults |
| `GET` | `/agent/welcome` | Return resolved welcome message |

### Knowledge Base

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/kb/documents` | List all documents with metadata |
| `GET` | `/kb/documents/{filename}` | Read document content |
| `POST` | `/kb/documents` | Upload document as JSON body |
| `POST` | `/kb/documents/upload-file` | Upload document as multipart file |
| `DELETE` | `/kb/documents/{filename}` | Delete a document |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser / User                      │
└──────────────────────────┬──────────────────────────────┘
                           │  HTTP :8501
┌──────────────────────────▼──────────────────────────────┐
│        Frontend  (Streamlit MPA — app.py router)        │
│                                                         │
│  Sidebar: backend status · KB doc count · agent info   │
│                                                         │
│  Page 1 — Chat                                          │
│    welcome screen (suggestions) → scrollable history    │
│    two-step render: instant user msg + spinner reply    │
│                                                         │
│  Page 2 — Knowledge Base                               │
│    upload / paste / delete docs · rebuild FAISS index   │
│                                                         │
│  Page 3 — Settings                                      │
│    Model Settings (service / provider, live)            │
│    Agent Configuration (identity + LLM params, saved)  │
│                                                         │
│  Page 4 — Docs                                          │
│    Built-in usage and API documentation                 │
└──────────────────────────┬──────────────────────────────┘
                           │  GET/POST /chat | /rag | /kb/... | /agent/...
                           │  HTTP :8000
┌──────────────────────────▼──────────────────────────────┐
│              Backend  (FastAPI — main.py)               │
│                                                         │
│   intent_service ──→ classify intent (7 categories)    │
│   agent_config_service ──→ load/save client config      │
│   kb_service ──→ document CRUD                          │
│                                                         │
│   ┌───────────────┐      ┌───────────────────────────┐  │
│   │ /chat         │      │ /rag                      │  │
│   │ langchain_    │      │ FAISS top-k retrieval     │  │
│   │ service.py    │      │ Intent-aware RAG prompt   │  │
│   │ (dynamic      │      │ Agent-config system prompt│  │
│   │  sys prompt)  │      └────────────┬──────────────┘  │
│   └──────┬────────┘                   │                  │
└──────────┼────────────────────────────┼──────────────────┘
           │                            │
┌──────────▼────────────────────────────▼──────────────────┐
│                     LLM Provider                         │
│   Groq (LLaMA 3.3 70B)  |  Mistral AI  |  HuggingFace   │
└──────────────────────────────────────────────────────────┘
```

---

## Backend API Reusability

The FastAPI backend is **fully decoupled from the Streamlit frontend** and can be consumed by any HTTP client. This makes it straightforward to integrate the support agent into existing products, services, or custom UIs without touching the backend code.

### Headless / API-only usage

Run the backend standalone and call it directly from any application:

```bash
cd backend
uvicorn main:app --reload
```

| Use case | How |
|---|---|
| Custom React / Vue / Angular frontend | Replace the Streamlit app entirely — call the same REST endpoints |
| Mobile app (iOS / Android) | Call `/rag` or `/chat` from any HTTP client |
| Slack / Teams bot | POST user messages to `/rag`, forward the response |
| CI pipeline knowledge checks | Automate `/rag` calls in test scripts to validate KB coverage |
| Zapier / Make webhook | Point an HTTP action at any `/chat` or `/rag` endpoint |
| Embedded widget | Wrap the RAG endpoint in a thin JS widget and embed it in any webpage |

### Key integration endpoints

```
POST /chat          — stateless LLM chat, no KB lookup
POST /rag           — grounded answer + intent label from the knowledge base
GET  /agent/config  — read current agent identity at runtime
POST /agent/config  — update agent identity/system-prompt without restart
GET  /kb/documents  — list all knowledge-base documents
POST /kb/documents/upload-file  — add new documents programmatically
POST /rag/rebuild   — re-index after uploading new documents
```

### Example: calling the RAG endpoint from Python

```python
import requests

res = requests.post(
    "http://localhost:8000/rag",
    json={
        "prompt": "How do I reset my password?",
        "provider": "groq",
        "history": [],          # pass previous turns for multi-turn support
    },
)
data = res.json()
print(data["response"])     # grounded answer
print(data["intent"])       # e.g. "Account & Login"
```

### Example: calling from JavaScript / TypeScript

```ts
const res = await fetch("http://localhost:8000/rag", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ prompt: "What's included in the Pro plan?", provider: "groq", history: [] }),
});
const { response, intent } = await res.json();
```

### Authentication (recommended before production)

The backend ships **without** authentication to keep the zero-config demo simple. Before exposing it publicly, add one of:

- **API key header** — FastAPI `Security` dependency that checks a secret `X-Client-Key` header
- **OAuth 2 / JWT** — `fastapi-users` or a reverse proxy (Nginx, Caddy, Traefik) in front of the service
- **Network isolation** — keep the backend on a private VPC or internal Docker network; only expose the frontend

---

## Customising for a New SaaS Client

1. **Update agent identity** — via **Settings > Agent Configuration** or `POST /agent/config`:
   ```json
   {
     "agent_name": "Aria",
     "company_name": "AcmeSaaS",
     "system_prompt": "You are Aria, support agent for AcmeSaaS. Be concise and professional.",
     "welcome_message": "Hi! I'm Aria from AcmeSaaS. How can I help?"
   }
   ```

2. **Upload product documentation** — via the **Knowledge Base** page or `POST /kb/documents`.

3. **Rebuild the vector index** — click **Rebuild Index** in the Knowledge Base page or call `POST /rag/rebuild`.

That's it — no code changes required.

---

## Intent Categories

| Intent | Emoji | Triggered by |
|---|---|---|
| Billing & Subscription | 💳 | pricing, invoice, payment, plan, upgrade |
| Troubleshooting | 🔧 | error, not working, crash, fix, issue |
| Account & Login | 🔐 | password, login, 2FA, locked, account |
| Integrations | 🔗 | Slack, Teams, Zapier, webhook, sync |
| API & Developer | ⚙️ | API, endpoint, rate limit, token, OAuth |
| Feature Request | 💡 | feature, suggest, would like, improve |
| General Inquiry | 💬 | everything else |

---

## Chat UI Behaviour

### Welcome state (no messages yet)
- Agent name and welcome message rendered **centered** on the page
- Four **suggestion chips** let users start a conversation with one click
- `st.chat_input` appears just below the centered content

### Active state (after first message)
- Chat history displayed in a **fixed-height (490 px) scrollable container** — layout never shifts as messages accumulate
- Input box anchored **directly below** the message area in a consistent position
- **Clear conversation** button between the message list and input bar

---

## Document Parsing — Roadmap

The current knowledge base only accepts plain `.md` and `.txt` files. The plan below outlines
phased support for richer document formats so teams can upload their existing content without
manual conversion.

### Phase 1 — Structured text (next)

| Format | Library | Notes |
|---|---|---|
| PDF | `pypdf` or `pdfminer.six` | Extract text per page; skip scanned/image-only PDFs |
| DOCX | `python-docx` | Paragraphs + tables; strip headers/footers |
| CSV / XLSX | `pandas` | Flatten rows into `field: value` text chunks |

Implementation touch-points:
- `kb_service.py` — add format detection by MIME type / extension before writing to `knowledge_base/`
- `POST /kb/documents/upload-file` — accept the new extensions in the `type=` filter
- Knowledge Base page — update the `st.file_uploader` accepted types list

### Phase 2 — Rich / scanned documents

| Format | Library | Notes |
|---|---|---|
| Scanned PDF / images | `pytesseract` + `Pillow` | OCR fallback when no text layer is detected |
| PowerPoint | `python-pptx` | Extract slide text and speaker notes |
| HTML / web pages | `beautifulsoup4` | Strip tags, keep visible text |

### Phase 3 — Remote sources

| Source | Approach | Notes |
|---|---|---|
| Confluence pages | Confluence REST API | Fetch page body as storage-format HTML, parse with BS4 |
| Notion docs | Notion API | Traverse block tree, export as Markdown |
| Google Docs | Google Drive API | Export as plain text or DOCX then parse via Phase 1 |
| GitHub repos | GitHub API / `gitpython` | Clone and index `.md` / `.rst` files from a repo |

### Chunking strategy (applies to all phases)

All parsed text will be split into overlapping chunks before embedding:

```
chunk_size    = 512 tokens
chunk_overlap = 64  tokens
splitter      = RecursiveCharacterTextSplitter (LangChain)
```

Metadata stored per chunk: `filename`, `page` (where applicable), `chunk_index`, `char_offset`.

### Required additions to `requirements.txt`

```
# Phase 1
pypdf>=4.0.0
python-docx>=1.1.0
pandas>=2.0.0
openpyxl>=3.1.0        # XLSX support for pandas

# Phase 2
pytesseract>=0.3.10
Pillow>=10.0.0
python-pptx>=0.6.23
beautifulsoup4>=4.12.0

# Phase 3 (as needed)
atlassian-python-api>=3.41.0
notion-client>=2.2.1
google-api-python-client>=2.100.0
```

---

## Testing

The project ships with a full pytest test suite that covers all API endpoints and every backend service. **No API keys or running services are required** — all LLM / RAG calls are mocked, and file-system operations are redirected to temporary directories.

### Test structure

```
backend/tests/
├── __init__.py
├── conftest.py                   # shared FastAPI TestClient fixture
├── test_api.py                   # 29 endpoint tests (all routes in main.py)
├── test_intent_service.py        # 34 unit tests — intent classification
├── test_kb_service.py            # 28 unit tests — KB document CRUD & path-safety
└── test_agent_config_service.py  # 20 unit tests — config load/save/reset/resolve
pytest.ini                        # testpaths + pythonpath configured
```

### pytest.ini

`pytest.ini` lives at the project root and configures three things:

| Option | Value | Purpose |
|---|---|---|
| `testpaths` | `backend/tests` | Tells pytest where to find tests when run from the project root — prevents it scanning the frontend, knowledge base, etc. |
| `pythonpath` | `backend` | Adds `backend/` to `sys.path` so test files can import `from services.intent_service import ...` or `from main import app` without relative-import hacks |
| `addopts` | `-v --tb=short` | Applies verbose output and compact tracebacks automatically on every run |

Without this file you would need to pass all of these on the command line every time:
```bash
python -m pytest backend/tests -v --tb=short
```

### Running the tests

```bash
# From the workspace root — run the full suite
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a single file
python -m pytest backend/tests/test_intent_service.py -v

# Run a single test class or function
python -m pytest backend/tests/test_api.py::test_health_returns_ok -v
```

### Test dependencies

`pytest` and `httpx` (required by FastAPI's `TestClient`) are listed in `requirements.txt` and installed automatically with `pip install -r requirements.txt`.

```
pytest>=8.0
httpx
```

### What is covered

| File | Scope | Mocking strategy |
|---|---|---|
| `test_api.py` | All REST endpoints — happy paths, error cases, auth | `unittest.mock.patch` on service functions; `monkeypatch` for env vars |
| `test_intent_service.py` | `classify_intent`, `get_intent_context` | None — pure keyword heuristics, no I/O |
| `test_kb_service.py` | `_safe_filename`, `save_document`, `get_document`, `delete_document`, `list_documents` | `tmp_path` + `monkeypatch` redirect `_KB_PATH` |
| `test_agent_config_service.py` | `get_config`, `update_config`, `reset_config`, `resolve_system_prompt`, `resolve_welcome_message` | `tmp_path` + `monkeypatch` redirect `_CONFIG_PATH` |

### API key authentication tests

The auth dependency is tested by reloading the `main` module with a monkeypatched `API_KEY` environment variable:

- No `API_KEY` set → all requests pass through (open mode)
- `API_KEY` set, no header → `403 Forbidden`
- `API_KEY` set, correct `X-Client-Key` header → `200 OK`
