from __future__ import annotations

import logging
from pathlib import Path

from src.modules.chat.application.knowledge.chunking import chunk_text
from src.modules.chat.application.knowledge.cleaning import (
    clean_text,
    strip_repeated_headers,
)
from src.modules.chat.application.knowledge.table_processing import (
    drop_total_and_note_rows,
    fill_merged_cells,
    rows_to_blocks,
)

logger = logging.getLogger(__name__)


def load_docx(path: Path) -> list[dict]:
    from docx import Document

    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = strip_repeated_headers(clean_text("\n".join(paragraphs)))
    return chunk_text(
        text,
        metadata={"document": path.name, "document_type": "docx"},
    )


def load_pdf(path: Path) -> list[dict]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        pages.append(page_text)
    text = strip_repeated_headers(clean_text("\n".join(pages)))
    return chunk_text(
        text,
        metadata={"document": path.name, "document_type": "pdf"},
    )


def load_xlsx(path: Path) -> list[dict]:
    from openpyxl import load_workbook

    wb = load_workbook(str(path), data_only=True)
    blocks: list[dict] = []
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        rows = [list(row) for row in sheet.iter_rows(values_only=True)]
        rows = [r for r in rows if any(c is not None and str(c).strip() != "" for c in r)]
        rows = fill_merged_cells(rows)
        rows = drop_total_and_note_rows(rows)
        if not rows:
            continue
        headers = [str(c or "") for c in rows[0]]
        blocks.extend(
            rows_to_blocks(rows, sheet=sheet_name, headers=headers)
        )
    return blocks


def load_text_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = strip_repeated_headers(clean_text(text))
    return chunk_text(
        text,
        metadata={"document": path.name, "document_type": "text"},
    )


def load_document(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return load_docx(path)
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix == ".xlsx":
        return load_xlsx(path)
    if suffix in {".txt", ".md"}:
        return load_text_file(path)
    raise ValueError(f"Định dạng không được hỗ trợ: {suffix}")
