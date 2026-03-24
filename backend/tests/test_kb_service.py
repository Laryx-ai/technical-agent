"""
Unit tests for services/kb_service.py.

File-system operations are performed inside a pytest tmp_path directory so
the real knowledge_base/ folder is never touched.
"""
import os
import pytest

import services.kb_service as kb_mod


@pytest.fixture(autouse=True)
def isolated_kb(tmp_path, monkeypatch):
    """Redirect all kb_service file operations to a fresh temp directory."""
    monkeypatch.setattr(kb_mod, "_KB_PATH", str(tmp_path))
    return tmp_path


# ===========================================================================
# _safe_filename  (internal helper)
# ===========================================================================

class TestSafeFilename:
    def test_valid_md_filename(self):
        assert kb_mod._safe_filename("my-doc.md") == "my-doc.md"

    def test_valid_txt_filename(self):
        assert kb_mod._safe_filename("notes_2026.txt") == "notes_2026.txt"

    def test_valid_pdf_filename(self):
        assert kb_mod._safe_filename("guide.pdf") == "guide.pdf"

    def test_strips_path_traversal_silently(self):
        # os.path.basename strips directory components; the result is just the filename
        result = kb_mod._safe_filename("../../../faq.md")
        assert result == "faq.md"

    def test_rejects_disallowed_extension(self):
        with pytest.raises(ValueError, match="not allowed"):
            kb_mod._safe_filename("script.exe")

    def test_rejects_html_extension(self):
        with pytest.raises(ValueError):
            kb_mod._safe_filename("page.html")

    def test_rejects_hidden_file(self):
        with pytest.raises(ValueError):
            kb_mod._safe_filename(".hidden")

    def test_rejects_special_characters_in_stem(self):
        with pytest.raises(ValueError):
            kb_mod._safe_filename("bad file!.md")

    def test_rejects_empty_filename(self):
        with pytest.raises(ValueError):
            kb_mod._safe_filename("")

    def test_strips_leading_path_component(self):
        # os.path.basename should strip the directory
        result = kb_mod._safe_filename("subdir/doc.md")
        assert result == "doc.md"


# ===========================================================================
# save_document
# ===========================================================================

class TestSaveDocument:
    def test_creates_file(self, isolated_kb):
        kb_mod.save_document("hello.md", "# Hello World")
        assert os.path.exists(isolated_kb / "hello.md")

    def test_returns_metadata(self, isolated_kb):
        meta = kb_mod.save_document("notes.txt", "some notes")
        assert meta["filename"] == "notes.txt"
        assert meta["size_bytes"] > 0
        assert meta["modified"].endswith("Z")

    def test_overwrites_existing_file(self, isolated_kb):
        kb_mod.save_document("file.md", "original")
        kb_mod.save_document("file.md", "updated content")
        content = (isolated_kb / "file.md").read_text(encoding="utf-8")
        assert content == "updated content"

    def test_rejects_disallowed_extension(self):
        with pytest.raises(ValueError):
            kb_mod.save_document("bad.py", "code")

    def test_path_traversal_is_stripped_to_basename(self, isolated_kb):
        # Path components are stripped; the file is written as "evil.md" in the KB dir
        meta = kb_mod.save_document("../../evil.md", "content")
        assert meta["filename"] == "evil.md"
        assert os.path.exists(isolated_kb / "evil.md")

    def test_saves_pdf_binary_content(self, isolated_kb):
        pdf_bytes = b"%PDF-1.4 test-pdf"
        meta = kb_mod.save_document("manual.pdf", pdf_bytes)
        assert meta["filename"] == "manual.pdf"
        assert (isolated_kb / "manual.pdf").read_bytes() == pdf_bytes


# ===========================================================================
# get_document
# ===========================================================================

class TestGetDocument:
    def test_reads_saved_content(self, isolated_kb):
        (isolated_kb / "faq.md").write_text("# FAQ\nContent", encoding="utf-8")
        content = kb_mod.get_document("faq.md")
        assert content == "# FAQ\nContent"

    def test_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            kb_mod.get_document("nonexistent.md")

    def test_path_traversal_stripped_then_raises_not_found(self):
        # basename strips "../"; file "escape.md" doesn't exist → FileNotFoundError
        with pytest.raises(FileNotFoundError):
            kb_mod.get_document("../escape.md")

    def test_extracts_text_from_pdf(self, isolated_kb, monkeypatch):
        (isolated_kb / "manual.pdf").write_bytes(b"%PDF-1.4 fake")

        class _Page:
            def __init__(self, text):
                self._text = text

            def extract_text(self):
                return self._text

        class _Reader:
            pages = [_Page("Intro"), _Page("Setup")]

        monkeypatch.setattr(kb_mod, "PdfReader", lambda _: _Reader())
        content = kb_mod.get_document("manual.pdf")
        assert content == "Intro\nSetup"


# ===========================================================================
# delete_document
# ===========================================================================

class TestDeleteDocument:
    def test_deletes_existing_file(self, isolated_kb):
        (isolated_kb / "old.md").write_text("old content", encoding="utf-8")
        kb_mod.delete_document("old.md")
        assert not os.path.exists(isolated_kb / "old.md")

    def test_returns_filename(self, isolated_kb):
        (isolated_kb / "target.md").write_text("data", encoding="utf-8")
        result = kb_mod.delete_document("target.md")
        assert result == "target.md"

    def test_raises_file_not_found_for_missing_file(self):
        with pytest.raises(FileNotFoundError):
            kb_mod.delete_document("ghost.md")

    def test_path_traversal_stripped_then_raises_not_found(self):
        # basename strips "../"; file "sneaky.md" doesn't exist → FileNotFoundError
        with pytest.raises(FileNotFoundError):
            kb_mod.delete_document("../sneaky.md")


# ===========================================================================
# list_documents
# ===========================================================================

class TestListDocuments:
    def test_returns_empty_for_empty_directory(self):
        assert kb_mod.list_documents() == []

    def test_returns_only_allowed_extensions(self, isolated_kb):
        (isolated_kb / "doc.md").write_text("a", encoding="utf-8")
        (isolated_kb / "notes.txt").write_text("b", encoding="utf-8")
        (isolated_kb / "script.py").write_text("c", encoding="utf-8")  # should be excluded
        docs = kb_mod.list_documents()
        filenames = [d["filename"] for d in docs]
        assert "doc.md" in filenames
        assert "notes.txt" in filenames
        assert "script.py" not in filenames

    def test_returned_metadata_has_required_fields(self, isolated_kb):
        (isolated_kb / "sample.md").write_text("sample", encoding="utf-8")
        docs = kb_mod.list_documents()
        assert len(docs) == 1
        doc = docs[0]
        assert doc["filename"] == "sample.md"
        assert doc["size_bytes"] > 0
        assert doc["modified"].endswith("Z")

    def test_results_are_sorted_alphabetically(self, isolated_kb):
        for name in ("zzz.md", "aaa.md", "mmm.txt"):
            (isolated_kb / name).write_text("x", encoding="utf-8")
        filenames = [d["filename"] for d in kb_mod.list_documents()]
        assert filenames == sorted(filenames)
