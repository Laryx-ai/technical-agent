import streamlit as st
from utils import api, sidebar_agent_info

FILE_UPLOAD_EXTENSIONS = {".md", ".txt", ".pdf"}
PASTE_EXTENSIONS = {".md", ".txt"}
MAX_FILE_SIZE_MB = 5
MIN_WORD_COUNT = 10


def _validate_upload(file_bytes: bytes, filename: str, existing_names: list[str]) -> str | None:
    """Return an error string if the uploaded file is invalid, else None."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in FILE_UPLOAD_EXTENSIONS:
        return f"Unsupported file type `{ext}`. Only .md, .txt, and .pdf files are allowed."
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return f"File is {size_mb:.1f} MB — the limit is {MAX_FILE_SIZE_MB} MB."
    if len(file_bytes) == 0:
        return "The file is empty."
    if ext != ".pdf":
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return "Text files must be UTF-8 encoded."
        if len(text.split()) < MIN_WORD_COUNT:
            return f"The file contains fewer than {MIN_WORD_COUNT} words and is unlikely to be useful for RAG."
    if filename in existing_names:
        return f"`{filename}` already exists in the knowledge base. Delete it first or choose a different name."
    return None


def _validate_paste(filename: str, content: str, existing_names: list[str]) -> str | None:
    """Return an error string if the pasted content is invalid, else None."""
    filename = filename.strip()
    if not filename:
        return "Please enter a filename."
    if "." not in filename:
        return "Filename must include an extension, e.g. `onboarding.md` or `notes.txt`."
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in PASTE_EXTENSIONS:
        return f"Unsupported file type `{ext}`. Only .md and .txt files are allowed."
    if any(c in filename for c in ('/\\:<>|?*"')):
        return "Filename contains invalid characters."
    if not content.strip():
        return "Document content is empty."
    size_mb = len(content.encode("utf-8")) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return f"Content is {size_mb:.1f} MB — the limit is {MAX_FILE_SIZE_MB} MB."
    if len(content.split()) < MIN_WORD_COUNT:
        return f"Content contains fewer than {MIN_WORD_COUNT} words and is unlikely to be useful for RAG."
    if filename in existing_names:
        return f"`{filename}` already exists in the knowledge base. Delete it first or choose a different name."
    return None

st.set_page_config(
    page_title="Knowledge Base — SaaS Support Agent",
    layout="wide",
)

sidebar_agent_info()

st.title("Knowledge Base")
st.caption(
    "Upload, view, or delete documents that the RAG agent uses to answer questions. "
    "After making changes, rebuild the index."
)
if "kb_flash_success" in st.session_state:
    st.toast(st.session_state.pop("kb_flash_success"), icon="✅")
if "kb_uploader_nonce" not in st.session_state:
    st.session_state["kb_uploader_nonce"] = 0
if "kb_removed_doc" in st.session_state:
    st.toast(st.session_state.pop("kb_removed_doc", None), icon="🗑️")

# Existing documents
st.subheader("Existing Documents")
docs_data, docs_err = api("get", "/kb/documents")
existing_names: list[str] = []

if docs_err:
    st.error(docs_err)
else:
    docs = (docs_data or {}).get("documents", [])
    existing_names = [doc["filename"] for doc in docs]
    if docs:
        for doc in docs:
            col1, col2, col3 = st.columns([4, 2, 1])
            col1.markdown(f"**{doc['filename']}**")
            col2.caption(f"{doc['size_bytes'] / 1024:.1f} KB · {doc['modified'][:10]}")
            if col3.button("Delete", key=f"del_{doc['filename']}", help="Delete document"):
                _, del_err = api("delete", f"/kb/documents/{doc['filename']}")
                if del_err:
                    st.error(del_err)
                else:
                    st.session_state["kb_removed_doc"] = (f"Deleted `{doc['filename']}`. Rebuild the index to apply changes.")
                    st.rerun()
    else:
        st.info("No documents in the knowledge base yet.")

st.divider()

# Upload
st.subheader("Upload a Document")
upload_col1, upload_col2 = st.columns(2)

with upload_col1:
    st.markdown("**Upload file** (.md, .txt, or .pdf, max 5 MB)")
    uploader_key = f"kb_upload_file_{st.session_state['kb_uploader_nonce']}"
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["md", "txt", "pdf"],
        label_visibility="collapsed",
        key=uploader_key,
    )
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        ext = "." + uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
        upload_err = _validate_upload(file_bytes, uploaded_file.name, existing_names)
        if upload_err:
            st.error(upload_err)
        else:
            if ext == ".pdf":
                st.caption(f"PDF detected · {len(file_bytes) / 1024:.1f} KB")
            else:
                text = file_bytes.decode("utf-8")
                preview = text[:300]
                st.caption(f"Preview: {len(text.split())} words · {len(file_bytes) / 1024:.1f} KB")
                st.code(preview + ("..." if len(text) > 300 else ""), language="markdown")
            if st.button("Upload", key="upload_file_btn"):
                mime_type = "application/pdf" if ext == ".pdf" else "text/plain"
                files = {"file": (uploaded_file.name, file_bytes, mime_type)}
                _, up_err = api("post", "/kb/documents/upload-file", files=files)
                if up_err:
                    st.error(up_err)
                else:
                    st.session_state["kb_flash_success"] = (
                        f"Uploaded `{uploaded_file.name}`. Rebuild the index to apply changes."
                    )
                    st.session_state["kb_uploader_nonce"] += 1
                    st.rerun()

with upload_col2:
    st.markdown("**Paste content directly**")
    doc_name = st.text_input("Filename (e.g. `onboarding.md`)", key="paste_filename")
    doc_content = st.text_area("Document content (Markdown or plain text)", height=160, key="paste_content")
    if st.button("Save document", key="save_paste_btn"):
        paste_err = _validate_paste(doc_name, doc_content, existing_names)
        if paste_err:
            st.error(paste_err)
        else:
            _, save_err = api("post", "/kb/documents", json={"filename": doc_name.strip(), "content": doc_content})
            if save_err:
                st.error(save_err)
            else:
                st.success(f"Saved `{doc_name.strip()}`. Rebuild the index to apply changes.")
                st.rerun()

st.divider()

# Rebuild index
st.subheader("Rebuild Vector Index")
st.caption("Run this after adding or deleting documents to update the RAG retrieval index.")
if st.button("Rebuild Index", type="primary", key="rebuild_btn"):
    with st.spinner("Rebuilding FAISS index…"):
        result, rebuild_err = api("post", "/rag/rebuild")
    if rebuild_err:
        st.error(rebuild_err)
    else:
        st.success((result or {}).get("message", "Index rebuilt."))
