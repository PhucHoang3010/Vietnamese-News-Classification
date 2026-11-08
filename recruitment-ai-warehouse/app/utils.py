"""Hàm tiện ích dùng chung: thời gian, xử lý chuỗi tiếng Việt."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def now_vn() -> datetime:
    """Thời điểm hiện tại theo giờ Việt Nam (naive datetime để lưu DB)."""
    return datetime.now(VN_TZ).replace(tzinfo=None, microsecond=0)


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt: 'Phỏng vấn Đợt 1' -> 'Phong van Dot 1'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_key(text: str | None) -> str:
    """Khoá so khớp: chữ thường, bỏ dấu, bỏ ký tự đặc biệt, gộp khoảng trắng."""
    if not text:
        return ""
    text = strip_accents(str(text)).lower()
    text = re.sub(r"[^a-z0-9+#]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def nfc(text: str | None) -> str:
    return unicodedata.normalize("NFC", text or "")
