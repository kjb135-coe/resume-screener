"""Turn a resume file on disk into raw text. No scoring logic here."""

from __future__ import annotations

from pathlib import Path


def load_resume_text(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(p))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix == ".docx":
        from docx import Document

        doc = Document(str(p))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    if suffix in (".txt", ".md"):
        return p.read_text(encoding="utf-8")

    raise ValueError(f"Unsupported resume format: {suffix}")


def iter_resume_paths(resume_dir: str) -> list[str]:
    supported = {".pdf", ".docx", ".txt", ".md"}
    return sorted(
        str(p) for p in Path(resume_dir).iterdir() if p.suffix.lower() in supported
    )
