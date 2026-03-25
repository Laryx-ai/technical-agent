import streamlit as st
from utils import sidebar_agent_info

st.set_page_config(
    page_title="Docs — SaaS Support Agent",
    layout="wide",
)

sidebar_agent_info()

st.title("Documentation")
st.caption("Everything you need to know about running and using this support agent.")

# Overview
st.header("Overview")
st.markdown("""
An AI-powered SaaS technical support agent that answers questions from your knowledge base
using Retrieval-Augmented Generation (RAG), classifies query intent, and lets you fully
customise the agent identity and LLM behaviour — all without restarting the server.

| Layer | Technology |
|---|---|
| Frontend | Streamlit multi-page app (`st.navigation()` router) |
| Backend | FastAPI + Uvicorn |
| LLM Orchestration | LangChain (LCEL) |
| LLM Providers | Groq (LLaMA 3.3 70B), Mistral AI, HuggingFace |
| Vector Store | FAISS |
| Embeddings | all-MiniLM-L6-v2 (sentence-transformers) |
| Intent Recognition | Keyword + heuristic classifier |
""")

st.divider()

# Pages
st.header("Pages")

with st.expander("Chat", expanded=True):
    st.markdown("""
The main conversation interface.

**Welcome screen** — shown when there is no conversation history. Displays the agent name,
welcome message, and four suggestion buttons. Clicking a suggestion sends it directly to the
agent in one click.

**Chat view** — once a message is sent the view switches to a scrollable history. Each
assistant reply shows the detected intent and the active service/provider.

**Two-step render** — your message appears instantly in the chat while the backend call
happens in the background, keeping the UI responsive.

**Input bar** — always pinned at the bottom. Disabled with a "Waiting for response…"
placeholder while the agent is thinking.

**Service and Provider** are read from the Settings page and applied to every message:
- **RAG** — answers grounded in the knowledge base. Works with `groq` and `mistral`.
- **Chat** — direct LLM conversation. Works with `groq`, `mistral`, and `hf`.
""")

with st.expander("Knowledge Base"):
    st.markdown("""
Manage the documents the RAG agent uses to answer questions.

**Supported formats:** `.md`, `.txt`, `.pdf`

**Existing documents** — listed with file size and last-modified date. Each row has a
**Delete** button that removes the file immediately.

**Upload a Document** — two options side by side:
- **Upload file** — browse and select a `.md`, `.txt`, or `.pdf` file.
- **Paste content** — type a filename and paste document content directly.

**Rebuild Index** — must be run after any add or delete to update the FAISS vector index.
Until you rebuild, the agent answers from the previous index.

Documents live in `backend/knowledge_base/`. The FAISS index is stored in `backend/faiss_index/`.
""")

with st.expander("Settings"):
    st.markdown("""
Two sections in one page — Model Settings and Agent Configuration.

---

**Model Settings** (live — changes apply immediately, no save needed)

| Field | Options | Effect |
|---|---|---|
| Service | `rag`, `chat` | RAG queries the knowledge base; Chat uses the LLM directly |
| Provider | `groq`, `mistral`, `hf` | Which LLM to call (`hf` only available in `chat` mode) |

The Chat page reads these values from session state on every message.

---

**Agent Configuration** (saved to `backend/agent_config.json`)

| Field | Description |
|---|---|
| Agent Name | Display name shown in the chat header and used in prompts |
| Company / Product Name | Inserted into the system prompt and welcome message |
| Welcome Message | Shown on the Chat welcome screen. Supports `{agent_name}` and `{company_name}` |
| System Prompt | Instruction given to the LLM before every conversation |
| Default LLM Provider | Fallback provider used when none is specified by the client |
| RAG Top-K | Number of document chunks retrieved per query (1–10) |
| Max History Turns | Previous conversation turns passed to the LLM (1–50) |

Use **Reset to Defaults** to restore the factory configuration.
""")

with st.expander("Docs"):
    st.markdown("""
This page. Built-in reference for setup, page descriptions, API endpoints, and
customisation instructions. No external link required.
""")

st.divider()

# Sidebar
st.header("Sidebar")
st.markdown("""
Visible on every page. Shows two live status signals:

- **Backend** — green dot when the FastAPI server responds to `/health`; red dot if unreachable.
- **Knowledge base** — green dot when at least one document exists; orange dot when empty.

The agent name, company, and version are shown as a caption at the very bottom of the sidebar.
""")

st.divider()

# Setup
st.header("Setup")

tab_local, tab_docker = st.tabs(["Local", "Docker"])

with tab_local:
    st.markdown("""
**1. Create and activate a virtual environment**
```bash
python -m venv venv
venv\\Scripts\\activate        # Windows
source venv/bin/activate     # macOS / Linux
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment variables**

Copy `.env.example` to `.env` and fill in your API keys:

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Groq LLaMA 3.3 70B — free key at console.groq.com |
| `MISTRAL_API_KEY` | Mistral AI chat + embeddings |
| `HF_TOKEN` | HuggingFace Inference API |
| `BACKEND_URL` | Frontend → backend URL (default: `http://localhost:8000`) |

**4. Start the backend**
```bash
cd backend
uvicorn main:app --reload
```
Runs at `http://localhost:8000` — interactive API docs at `/docs`.

**5. Start the frontend**
```bash
cd frontend
streamlit run app.py
```
Runs at `http://localhost:8501`.
""")

with tab_docker:
    st.markdown("""
**Start both services**
```bash
docker-compose up --build
```

**Detached mode**
```bash
docker-compose up -d --build
```

**View logs**
```bash
docker-compose logs -f
```

**Stop**
```bash
docker-compose down
```

- Backend on port **8000**
- Frontend on port **8501**
- FAISS index, knowledge base, and agent config are mounted as volumes — data persists across restarts.
""")

# Customising for a client
st.header("Customising for a New Client")
st.markdown("""
1. Go to **Settings > Agent Configuration** and set the agent name, company, welcome message, and system prompt.
2. Go to **Knowledge Base** and upload your product documentation (`.md`, `.txt`, or `.pdf`).
3. Click **Rebuild Index** in the Knowledge Base page.

That's it — no code changes required. The agent picks up the new identity and knowledge on the next message.

> ⚠️ **Important**: The RAG system only answers from uploaded documents. If the knowledge base is empty or lacks content on a topic, the LLM will not have that information. Always populate the knowledge base with your actual product documentation before expecting accurate responses.
""")

st.divider()

# API Reference
st.header("API Reference")
st.caption("Base URL: `http://localhost:8000`  ·  Interactive docs: `/docs`")

with st.expander("System"):
    st.markdown("""
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — returns `agent`, `company`, `version` |
""")

with st.expander("Chat"):
    st.markdown("""
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Direct LLM chat (`groq` / `mistral` / `hf`) |
| `POST` | `/rag` | Knowledge base-grounded chat with intent detection |
| `POST` | `/rag/rebuild` | Rebuild FAISS index from `knowledge_base/` |

**Request body for `/chat` and `/rag`:**
```json
{
  "prompt": "How do I reset my password?",
  "provider": "groq",
  "history": [
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Response from `/rag`:**
```json
{
  "response":     "Here is how to reset your password…",
  "intent_label": "Account & Login",
}
```
""")

with st.expander("Intent"):
    st.markdown("""
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/intent` | Classify query intent without generating a response |

**Request body:**
```json
{ "text": "Why is my invoice wrong?" }
```

**Response:**
```json
{
  "intent":     "billing",
  "label":      "Billing",
  "confidence": 0.95
}
```

**Intent categories:**

| Intent | Triggered by |
|---|---|
| Billing & Subscription | pricing, invoice, payment, plan, upgrade |
| Troubleshooting | error, not working, crash, fix, issue |
| Account & Login | password, login, 2FA, locked, account |
| Integrations | Slack, Teams, Zapier, webhook, sync |
| API & Developer | API, endpoint, rate limit, token, OAuth |
| Feature Request | feature, suggest, would like, improve |
| General Inquiry | everything else |
""")

with st.expander("Agent Configuration"):
    st.markdown("""
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/agent/config` | Read current configuration |
| `POST` | `/agent/config` | Update one or more fields |
| `POST` | `/agent/config/reset` | Restore factory defaults |
| `GET` | `/agent/welcome` | Return resolved welcome message |

**Updatable fields:**
```json
{
  "agent_name":        "Aria",
  "company_name":      "AcmeSaaS",
  "welcome_message":   "Hi! I'm {agent_name} from {company_name}. How can I help?",
  "system_prompt":     "You are {agent_name}…",
  "llm_provider":      "groq",
  "rag_top_k":         4,
  "max_history_turns": 10
}
```
""")

with st.expander("Knowledge Base"):
    st.markdown("""
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/kb/documents` | List all documents with metadata |
| `GET` | `/kb/documents/{filename}` | Read a single document |
| `POST` | `/kb/documents` | Save a document by content (JSON body) |
| `POST` | `/kb/documents/upload-file` | Upload a `.md`, `.txt`, or `.pdf` file (multipart) |
| `DELETE` | `/kb/documents/{filename}` | Delete a document |
""")
