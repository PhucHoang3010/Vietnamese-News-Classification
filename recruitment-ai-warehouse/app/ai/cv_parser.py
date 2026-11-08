"""Trích văn bản từ CV (PDF, DOCX, TXT/MD) và tách các trường cơ bản."""
from __future__ import annotations

import io
import re
from pathlib import Path

from app.etl.normalize import normalize_education, parse_years_experience
from app.utils import nfc, strip_accents


def extract_text(data: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == ".docx":
        import docx

        document = docx.Document(io.BytesIO(data))
        parts = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        text = "\n".join(parts)
    elif suffix in {".txt", ".md", ".text", ""}:
        for encoding in ("utf-8-sig", "utf-16", "cp1258", "latin-1"):
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
    else:
        raise ValueError(f"Định dạng CV chưa hỗ trợ: {suffix}")
    return clean_cv_text(text)


def extract_text_from_path(path: Path) -> str:
    return extract_text(path.read_bytes(), path.name)


def clean_cv_text(text: str) -> str:
    text = nfc(text).replace("\r", "\n").replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def guess_years_experience(text: str) -> float | None:
    plain = strip_accents(text).lower()
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*\+?\s*(?:nam|years?)\s*(?:kinh nghiem|experience|of experience)", plain)
    if match:
        return parse_years_experience(match.group(1))
    match = re.search(r"kinh nghiem[^\n:]*:\s*(\d+(?:[.,]\d+)?)", plain)
    if match:
        return parse_years_experience(match.group(1))
    return None


def guess_education(text: str) -> str | None:
    for line in text.splitlines():
        plain = strip_accents(line).lower()
        if any(k in plain for k in ["dai hoc", "thac si", "cao dang", "university", "bachelor", "master", "cu nhan",
                                    "ky su", "tien si"]):
            level = normalize_education(line)
            if level:
                return level
    return None


SECTION_HEADERS = {
    "objective": ["muc tieu", "objective", "career objective", "gioi thieu ban than", "summary"],
    "experience": ["kinh nghiem lam viec", "kinh nghiem", "work experience", "experience"],
    "education": ["hoc van", "education", "trinh do hoc van"],
    "skills": ["ky nang", "skills", "technical skills"],
    "projects": ["du an", "projects"],
    "certificates": ["chung chi", "certificates", "certifications", "giai thuong"],
}


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        plain = strip_accents(line).lower().strip(" :-•*#")
        found = None
        if len(plain) < 40:
            for name, headers in SECTION_HEADERS.items():
                if plain in headers:
                    found = name
                    break
        if found:
            current = found
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}
