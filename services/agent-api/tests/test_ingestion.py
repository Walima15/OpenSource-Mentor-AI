"""Offline tests for ingestion chunking and file filtering."""

from __future__ import annotations

from app.services.ingestion_service import (
    CHUNK_LINES,
    MAX_FILE_BYTES,
    _chunk_file,
    _is_indexable,
)


def test_is_indexable_accepts_source_files():
    assert _is_indexable("app/main.py", 1000)
    assert _is_indexable("src/index.ts", 500)
    assert _is_indexable("README.md", 200)


def test_is_indexable_rejects_unknown_extensions():
    assert not _is_indexable("image.png", 100)
    assert not _is_indexable("data.bin", 100)


def test_is_indexable_rejects_vendored_and_minified():
    assert not _is_indexable("node_modules/x/index.js", 100)
    assert not _is_indexable("dist/bundle.js", 100)
    assert not _is_indexable("app.min.js", 100)


def test_is_indexable_rejects_oversized_files():
    assert not _is_indexable("big.py", MAX_FILE_BYTES + 1)
    # Unknown size should not disqualify a file.
    assert _is_indexable("app.py", None)


def test_chunk_file_produces_line_ranges():
    content = "\n".join(f"line{i}" for i in range(1, 151))
    chunks = _chunk_file("f.py", content)
    assert chunks
    assert all(c["file_path"] == "f.py" for c in chunks)
    first = chunks[0]
    assert first["start_line"] == 1
    assert first["end_line"] <= CHUNK_LINES
    # Chunks should cover the file and be non-empty.
    assert all(c["content"].strip() for c in chunks)


def test_chunk_file_skips_empty_content():
    assert _chunk_file("f.py", "") == []
    assert _chunk_file("f.py", "\n\n\n") == []
