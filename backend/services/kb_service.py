"""
kb_service.py — Knowledge Base Document Management

Manages the lifecycle of documents in the knowledge_base/ folder:
  - List existing documents with metadata
  - Save uploaded documents (text / markdown / pdf)
  - Delete documents
  - Trigger FAISS index rebuild after changes

All file writes are restricted to the knowledge_base directory to
prevent path-traversal attacks.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from pypdf import PdfReader

_KB_PATH = os.path.join(os.path.dirname(__file__), "../knowledge_base")
_ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}


def _safe_filename(name: str) -> str:
    """
    Sanitise a filename: keep only alphanum, dash, underscore, dot.
    Raises ValueError for path-traversal attempts or disallowed extensions.
    """
    # Strip to basename and reject path separators
    name = os.path.basename(name)
    if not name or name.startswith("."):
        raise ValueError("Invalid filename.")

    ext = os.path.splitext(name)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension '{ext}' is not allowed. Use .md , .txt , .pdf")

    # Allow only safe characters in the stem
    stem = os.path.splitext(name)[0]
    if not re.match(r"^[A-Za-z0-9_\-]+$", stem):
        raise ValueError("Filename may only contain letters, digits, hyphens and underscores.")

    return name


def list_documents() -> list[dict]:
    """Return metadata for every document in the knowledge base."""
    docs = []
    for fname in sorted(os.listdir(_KB_PATH)):
        ext = os.path.splitext(fname)[1].lower()
        if ext not in _ALLOWED_EXTENSIONS:
            continue
        fpath = os.path.join(_KB_PATH, fname)
        stat = os.stat(fpath)
        docs.append({
            "filename": fname,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z",
        })
    return docs


def save_document(filename: str, content: str | bytes) -> dict:
    """
    Write *content* to knowledge_base/<filename>.
    Returns document metadata.
    Raises ValueError for unsafe filenames or disallowed extensions.
    """
    safe_name = _safe_filename(filename)
    dest = os.path.join(_KB_PATH, safe_name)
    ext = os.path.splitext(safe_name)[1].lower()

    if ext == ".pdf":
        if not isinstance(content, (bytes, bytearray)):
            raise ValueError("PDF uploads must be binary file content.")
        with open(dest, "wb") as f:
            f.write(content)
    else:
        text_content: str
        if isinstance(content, str):
            text_content = content
        elif isinstance(content, (bytes, bytearray, memoryview)):
            try:
                text_content = bytes(content).decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValueError("Text files must be UTF-8 encoded.") from e
        else:
            raise ValueError("Text uploads must be string or UTF-8 bytes.")

        with open(dest, "w", encoding="utf-8") as f:
            f.write(text_content)
    stat = os.stat(dest)
    return {
        "filename": safe_name,
        "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z",
    }


def delete_document(filename: str) -> str:
    """
    Delete knowledge_base/<filename>.
    Raises FileNotFoundError if the document doesn't exist.
    Raises ValueError for unsafe filenames.
    """
    safe_name = _safe_filename(filename)
    target = os.path.join(_KB_PATH, safe_name)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"Document '{safe_name}' not found.")
    os.remove(target)
    return safe_name


def get_document(filename: str) -> str:
    """Return the raw text content of a knowledge base document."""
    safe_name = _safe_filename(filename)
    target = os.path.join(_KB_PATH, safe_name)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"Document '{safe_name}' not found.")
    ext = os.path.splitext(safe_name)[1].lower()
    if ext == ".pdf":
        with open(target, "rb") as f:
            reader = PdfReader(f)
            return "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    with open(target, "r", encoding="utf-8") as f:
        return f.read()
