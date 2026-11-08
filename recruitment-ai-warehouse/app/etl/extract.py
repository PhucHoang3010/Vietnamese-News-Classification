"""EXTRACT – đọc dữ liệu thô từ 4 loại nguồn rời rạc.

  * GOOGLE_FORM : file CSV xuất từ Google Form ứng tuyển
  * ATS         : file JSON xuất từ hệ thống ATS (gồm danh mục vị trí + hồ sơ + lịch sử vòng)
  * EXCEL       : file Excel HR tự theo dõi (tiêu đề có thể không nằm ở dòng đầu)
  * EMAIL       : file .eml hộp thư tuyển dụng (ứng tuyển / rút hồ sơ, kèm CV đính kèm)
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.ai.cv_parser import extract_text
from app.utils import normalize_key

CV_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@dataclass
class RawItem:
    source_system: str
    source_file: str
    record_no: int
    payload: dict[str, Any]


@dataclass
class ExtractResult:
    items: list[RawItem] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat() if not pd.isna(value) else None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (int, float, bool, str)):
        return value
    return str(value)


def detect_source(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "GOOGLE_FORM"
    if suffix == ".json":
        return "ATS"
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return "EXCEL"
    if suffix == ".eml":
        return "EMAIL"
    if suffix in CV_EXTENSIONS:
        return "CV_FILE"
    return None


def extract_google_form(path: Path) -> ExtractResult:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    result = ExtractResult()
    for i, row in enumerate(df.to_dict(orient="records"), start=2):  # dòng 1 là tiêu đề
        result.items.append(RawItem("GOOGLE_FORM", path.name, i, {k.strip(): _clean_value(v) for k, v in row.items()}))
    result.messages.append(f"{path.name}: {len(df)} câu trả lời Google Form, {len(df.columns)} cột")
    return result


def extract_ats(path: Path) -> ExtractResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = ExtractResult()
    for i, job in enumerate(data.get("jobs", []), start=1):
        result.items.append(RawItem("ATS_JOB", path.name, i, job))
    for i, app in enumerate(data.get("applications", []), start=1):
        result.items.append(RawItem("ATS", path.name, i, app))
    result.messages.append(
        f"{path.name}: {len(data.get('jobs', []))} vị trí, {len(data.get('applications', []))} hồ sơ ATS "
        f"(xuất lúc {data.get('exported_at', '?')})"
    )
    return result


def extract_excel(path: Path) -> ExtractResult:
    result = ExtractResult()
    sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object)
    for sheet_name, raw in sheets.items():
        header_row = None
        for idx in range(min(len(raw), 15)):
            cells = [normalize_key(str(c)) for c in raw.iloc[idx].tolist() if c is not None and str(c) != "nan"]
            if any(c in {"ho ten", "ho va ten", "ho ten ung vien", "ten ung vien"} for c in cells):
                header_row = idx
                break
        if header_row is None:
            result.messages.append(f"{path.name}/{sheet_name}: bỏ qua (không tìm thấy dòng tiêu đề)")
            continue
        headers = [str(c).strip() if c is not None and str(c) != "nan" else f"col_{j}"
                   for j, c in enumerate(raw.iloc[header_row].tolist())]
        body = raw.iloc[header_row + 1:]
        count = 0
        for offset, (_, row) in enumerate(body.iterrows(), start=header_row + 2):
            values = {headers[j]: _clean_value(v) for j, v in enumerate(row.tolist())}
            if not any(v not in (None, "") for k, v in values.items() if not k.lower().startswith(("stt", "col_"))):
                continue  # dòng trống
            values["_sheet"] = sheet_name
            result.items.append(RawItem("EXCEL", path.name, offset, values))
            count += 1
        result.messages.append(
            f"{path.name}/{sheet_name}: {count} dòng dữ liệu (phát hiện tiêu đề ở dòng {header_row + 1})"
        )
    return result


def extract_email(path: Path, record_no: int = 1) -> ExtractResult:
    msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    sender_name, sender_email = parseaddr(msg.get("From", ""))
    body_part = msg.get_body(preferencelist=("plain", "html"))
    body = body_part.get_content() if body_part else ""
    attachments = []
    for part in msg.iter_attachments():
        filename = part.get_filename() or "attachment"
        payload = part.get_payload(decode=True) or b""
        entry = {"filename": filename, "size": len(payload)}
        if Path(filename).suffix.lower() in CV_EXTENSIONS:
            try:
                entry["text"] = extract_text(payload, filename)
            except Exception as exc:  # noqa: BLE001
                entry["error"] = str(exc)
        attachments.append(entry)
    try:
        sent_at = parsedate_to_datetime(msg.get("Date")).isoformat() if msg.get("Date") else None
    except (TypeError, ValueError):
        sent_at = None
    payload = {
        "message_id": msg.get("Message-ID"),
        "from_name": sender_name,
        "from_email": sender_email,
        "subject": str(msg.get("Subject", "")),
        "date": sent_at,
        "body": body,
        "attachments": attachments,
    }
    return ExtractResult(items=[RawItem("EMAIL", path.name, record_no, payload)])


def extract_file(path: Path) -> ExtractResult:
    source = detect_source(path)
    if source == "GOOGLE_FORM":
        return extract_google_form(path)
    if source == "ATS":
        return extract_ats(path)
    if source == "EXCEL":
        return extract_excel(path)
    if source == "EMAIL":
        return extract_email(path)
    return ExtractResult(messages=[f"{path.name}: bỏ qua (định dạng không thuộc nguồn dữ liệu)"])


class CvLocator:
    """Tìm và đọc file CV được tham chiếu trong form/ATS (theo tên file)."""

    def __init__(self, folders: list[Path]):
        self.index: dict[str, Path] = {}
        for folder in folders:
            if folder.exists():
                for p in folder.rglob("*"):
                    if p.is_file() and p.suffix.lower() in CV_EXTENSIONS:
                        self.index.setdefault(p.name.lower(), p)
        self._cache: dict[str, str | None] = {}

    def read(self, reference: str | None) -> tuple[str | None, str | None]:
        if not reference:
            return None, None
        name = Path(str(reference).replace("\\", "/")).name.lower()
        if name not in self._cache:
            path = self.index.get(name)
            text = None
            if path:
                try:
                    text = extract_text(path.read_bytes(), path.name)
                except Exception:  # noqa: BLE001
                    text = None
            self._cache[name] = text
        return self._cache[name], (Path(str(reference)).name if self._cache[name] else None)
