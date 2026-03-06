import streamlit as st
from utils import api, sidebar_agent_info

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

# Existing documents
st.subheader("Existing Documents")
docs_data, docs_err = api("get", "/kb/documents")

if docs_err:
    st.error(docs_err)
else:
    docs = (docs_data or {}).get("documents", [])
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
                    st.success(f"Deleted `{doc['filename']}`.")
                    st.rerun()
    else:
        st.info("No documents in the knowledge base yet.")

st.divider()

# Upload
st.subheader("Upload a Document")
upload_col1, upload_col2 = st.columns(2)

with upload_col1:
    st.markdown("**Upload file** (.md or .txt)")
    uploaded_file = st.file_uploader("Choose a file", type=["md", "txt"], label_visibility="collapsed")
    if uploaded_file and st.button("Upload", key="upload_file_btn"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
        _, up_err = api("post", "/kb/documents/upload-file", files=files)
        if up_err:
            st.error(up_err)
        else:
            st.success(f"Uploaded `{uploaded_file.name}`. Rebuild the index to apply changes.")
            st.rerun()

with upload_col2:
    st.markdown("**Paste content directly**")
    doc_name = st.text_input("Filename (e.g. `onboarding.md`)", key="paste_filename")
    doc_content = st.text_area("Document content (Markdown or plain text)", height=160, key="paste_content")
    if st.button("Save document", key="save_paste_btn"):
        if not doc_name.strip():
            st.warning("Please enter a filename.")
        elif not doc_content.strip():
            st.warning("Document content is empty.")
        else:
            _, save_err = api("post", "/kb/documents", json={"filename": doc_name, "content": doc_content})
            if save_err:
                st.error(save_err)
            else:
                st.success(f"Saved `{doc_name}`. Rebuild the index to apply changes.")
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
