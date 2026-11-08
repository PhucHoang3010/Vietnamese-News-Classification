"""Ẩn danh hoá CV trước khi đưa cho AI (chống thiên vị & bảo vệ dữ liệu cá nhân).

Loại bỏ: họ tên, email, số điện thoại, ngày sinh/tuổi, giới tính, tình trạng hôn nhân,
quê quán/địa chỉ, tôn giáo, dân tộc, sức khoẻ, ảnh, đường link mạng xã hội.
"""
from __future__ import annotations

import re

from app.utils import strip_accents

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?:\+?84|0)(?:[\s.\-]?\d){8,10}")
URL_RE = re.compile(r"(?:https?://|www\.)\S+|(?:linkedin|facebook|github)\.com/\S+", re.I)
DATE_RE = re.compile(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.](?:19|20)\d{2}\b")
AGE_RE = re.compile(r"\b\d{2}\s*tuổi\b", re.I)

# Nhãn dòng chứa thuộc tính nhạy cảm (so khớp sau khi bỏ dấu, chữ thường)
SENSITIVE_LABELS: dict[str, list[str]] = {
    "ho_ten": ["ho va ten", "ho ten", "full name", "name"],
    "ngay_sinh": ["ngay sinh", "nam sinh", "date of birth", "dob", "birthday", "tuoi", "age"],
    "gioi_tinh": ["gioi tinh", "gender", "sex"],
    "hon_nhan": ["tinh trang hon nhan", "hon nhan", "marital status", "gia dinh"],
    "dia_chi": ["dia chi", "address", "noi o", "cho o", "thuong tru", "tam tru", "que quan", "nguyen quan",
                "hometown", "noi sinh"],
    "ton_giao": ["ton giao", "religion"],
    "dan_toc": ["dan toc", "ethnicity", "quoc tich", "nationality"],
    "suc_khoe": ["suc khoe", "health", "chieu cao", "can nang", "height", "weight"],
    "anh": ["anh the", "anh chan dung", "photo"],
    "lien_he": ["so dien thoai", "dien thoai", "phone", "sdt", "email", "mobile", "zalo"],
}


def _line_label(line: str) -> str | None:
    head = strip_accents(line.split(":", 1)[0]).lower().strip(" -•*\t")
    if ":" not in line or len(head) > 40:
        return None
    for field, labels in SENSITIVE_LABELS.items():
        if any(head == lab or head.endswith(" " + lab) or head.startswith(lab + " ") for lab in labels):
            return field
    return None


def anonymize_text(text: str | None, names: list[str] | None = None) -> tuple[str, list[str]]:
    """Trả về (văn bản đã ẩn danh, danh sách loại thông tin đã loại bỏ)."""
    if not text:
        return "", []
    removed: set[str] = set()
    kept_lines = []
    for line in text.splitlines():
        field = _line_label(line)
        if field:
            removed.add(field)
            kept_lines.append(f"[{field.upper()} – đã ẩn]")
            continue
        kept_lines.append(line)
    result = "\n".join(kept_lines)

    for pattern, field, repl in [
        (EMAIL_RE, "lien_he", "[EMAIL]"),
        (URL_RE, "lien_ket", "[LINK]"),
        (PHONE_RE, "lien_he", "[SĐT]"),
        (DATE_RE, "ngay_sinh", "[NGÀY]"),
        (AGE_RE, "ngay_sinh", "[TUỔI]"),
    ]:
        if pattern.search(result):
            removed.add(field)
            result = pattern.sub(repl, result)

    for name in names or []:
        if name and len(name) > 2:
            if re.search(re.escape(name), result, re.I):
                removed.add("ho_ten")
            result = re.sub(re.escape(name), "[ỨNG VIÊN]", result, flags=re.I)
            # Ẩn cả tên viết hoa toàn bộ (thường đặt ở đầu CV)
            result = re.sub(re.escape(name.upper()), "[ỨNG VIÊN]", result)
    return result.strip(), sorted(removed)
