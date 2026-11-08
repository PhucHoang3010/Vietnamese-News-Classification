"""Các hàm chuẩn hoá dữ liệu ứng viên (Transform).

Mỗi hàm nhận giá trị "bẩn" từ nguồn bất kỳ và trả về giá trị chuẩn hoặc None.
"""
from __future__ import annotations

import difflib
import math
import re
from datetime import date, datetime, timedelta
from typing import Any

from app.reference import (
    CITY_ALIASES,
    EDUCATION_ALIASES,
    OUTCOME_ALIASES,
    SOURCES,
    STAGES,
    STATUS_ALIASES,
)
from app.utils import VN_TZ, nfc, normalize_key

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and value.strip() in {"", "-", "nan", "NaN", "None", "N/A", "n/a"}


def clean_str(value: Any) -> str | None:
    if is_blank(value):
        return None
    text = nfc(str(value)).strip()
    return re.sub(r"\s+", " ", text) or None


# --------------------------------------------------------------------------- #
# Thông tin định danh
# --------------------------------------------------------------------------- #
def normalize_name(value: Any) -> str | None:
    text = clean_str(value)
    if not text:
        return None
    text = re.sub(r"[^\w\s'.-]", " ", text)
    words = [w for w in text.split() if w]
    return " ".join(w[:1].upper() + w[1:].lower() for w in words) or None


def normalize_email(value: Any) -> str | None:
    text = clean_str(value)
    if not text:
        return None
    # "Nguyễn Văn A <a@gmail.com>" -> a@gmail.com
    match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    if not match:
        return None
    email = match.group(0).lower().strip(".")
    return email if EMAIL_RE.match(email) else None


def normalize_phone(value: Any) -> str | None:
    """Chuẩn hoá số di động Việt Nam về dạng 0xxxxxxxxx (10 số)."""
    if is_blank(value):
        return None
    if isinstance(value, float):
        value = f"{value:.0f}"
    digits = re.sub(r"\D", "", str(value))
    if digits.startswith("84") and len(digits) == 11:
        digits = "0" + digits[2:]
    elif len(digits) == 9 and not digits.startswith("0"):
        digits = "0" + digits
    if len(digits) == 10 and digits.startswith("0") and digits[1] in "35789":
        return digits
    return None


def normalize_gender(value: Any) -> str | None:
    key = normalize_key(clean_str(value))
    if key in {"nam", "male", "m", "trai", "gioi tinh nam"}:
        return "Nam"
    if key in {"nu", "female", "f", "gai", "gioi tinh nu"}:
        return "Nữ"
    if key in {"khac", "other"}:
        return "Khác"
    return None


# --------------------------------------------------------------------------- #
# Ngày giờ
# --------------------------------------------------------------------------- #
_DT_FORMATS = [
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d-%m-%Y %H:%M", "%d-%m-%Y", "%d.%m.%Y",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%y",
]


def parse_datetime(value: Any) -> datetime | None:
    """Đọc ngày giờ từ nhiều định dạng: ISO, dd/mm/yyyy, số serial Excel, Timestamp."""
    if is_blank(value):
        return None
    if hasattr(value, "to_pydatetime"):  # pandas.Timestamp
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(VN_TZ).replace(tzinfo=None)
        return value.replace(microsecond=0)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, (int, float)) and 20000 < float(value) < 80000:  # serial date của Excel
        return datetime(1899, 12, 30) + timedelta(days=float(value))
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(VN_TZ).replace(tzinfo=None)
        return parsed.replace(microsecond=0)
    except ValueError:
        pass
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_date(value: Any) -> date | None:
    parsed = parse_datetime(value)
    return parsed.date() if parsed else None


# --------------------------------------------------------------------------- #
# Thuộc tính nghề nghiệp
# --------------------------------------------------------------------------- #
def parse_years_experience(value: Any) -> float | None:
    if is_blank(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    key = normalize_key(str(value)).replace(",", ".")
    if any(k in key for k in ["chua co", "fresher", "khong co", "moi tot nghiep", "sinh vien", "intern"]):
        return 0.0
    numbers = [float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", str(value))]
    if not numbers:
        return None
    if "duoi" in key and len(numbers) == 1:
        return max(numbers[0] - 0.5, 0.0)
    if len(numbers) >= 2:
        return round((numbers[0] + numbers[1]) / 2, 1)
    return numbers[0]


def parse_salary_million(value: Any) -> float | None:
    """'15 triệu' | '15tr' | '15.000.000' | '15-18 triệu' -> triệu VND."""
    if is_blank(value):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return round(number / 1_000_000, 1) if number > 1000 else number
    text = str(value).lower()
    if "thoa thuan" in normalize_key(text) or "deal" in text:
        return None
    compact = text.replace(" ", "")
    numbers = re.findall(r"\d+(?:[.,]\d+)*", compact)
    values: list[float] = []
    for raw in numbers:
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", raw):  # 15.000.000
            values.append(float(re.sub(r"[.,]", "", raw)) / 1_000_000)
        else:
            number = float(raw.replace(",", "."))
            values.append(number / 1_000_000 if number > 1000 else number)
    if not values:
        return None
    return round(sum(values[:2]) / len(values[:2]), 1)


def _alias_pairs(mapping: dict[str, list[str]]) -> list[tuple[str, str]]:
    pairs = [(normalize_key(alias), code) for code, aliases in mapping.items() for alias in aliases]
    pairs += [(normalize_key(code), code) for code in mapping]
    return sorted(set(pairs), key=lambda p: len(p[0]), reverse=True)


def match_alias(value: Any, pairs: list[tuple[str, str]], fuzzy_cutoff: float = 0.85) -> str | None:
    """So khớp chuỗi với bảng biến thể: khớp chính xác -> chứa cụm từ -> gần đúng (difflib)."""
    key = normalize_key(clean_str(value))
    if not key:
        return None
    lookup = dict(pairs)
    if key in lookup:
        return lookup[key]
    padded = f" {key} "
    for alias, code in pairs:  # đã sắp xếp theo độ dài giảm dần
        if alias and f" {alias} " in padded:
            return code
    close = difflib.get_close_matches(key, list(lookup), n=1, cutoff=fuzzy_cutoff)
    return lookup[close[0]] if close else None


_CITY_PAIRS = _alias_pairs(CITY_ALIASES)
_EDU_PAIRS = _alias_pairs(EDUCATION_ALIASES)
_STATUS_PAIRS = _alias_pairs(STATUS_ALIASES)
_OUTCOME_PAIRS = _alias_pairs(OUTCOME_ALIASES)
_SOURCE_PAIRS = _alias_pairs({code: aliases + [name] for code, name, _ch, aliases in SOURCES})
_STAGE_PAIRS = _alias_pairs({code: aliases + [name] for code, name, *_rest, aliases in STAGES})


def normalize_city(value: Any) -> str | None:
    text = clean_str(value)
    if not text:
        return None
    code = match_alias(text, _CITY_PAIRS, fuzzy_cutoff=0.8)
    return code or normalize_name(text)


def normalize_education(value: Any) -> str | None:
    return match_alias(value, _EDU_PAIRS, fuzzy_cutoff=0.8)


def map_source(value: Any) -> str:
    return match_alias(value, _SOURCE_PAIRS, fuzzy_cutoff=0.8) or "OTHER"


def map_stage(value: Any) -> str | None:
    return match_alias(value, _STAGE_PAIRS, fuzzy_cutoff=0.8)


def map_status(value: Any) -> str | None:
    return match_alias(value, _STATUS_PAIRS, fuzzy_cutoff=0.85)


def map_outcome(value: Any) -> str | None:
    return match_alias(value, _OUTCOME_PAIRS, fuzzy_cutoff=0.85)


def parse_score(value: Any) -> float | None:
    """Điểm phỏng vấn quy về thang 1–5 (chấp nhận '4/5', '8/10', '80%')."""
    if is_blank(value):
        return None
    text = str(value).replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:/\s*(\d+))?\s*(%)?", text)
    if not match:
        return None
    number = float(match.group(1))
    if match.group(3):
        number = number / 20
    elif match.group(2):
        number = number / float(match.group(2)) * 5
    elif number > 5:
        number = number / 2 if number <= 10 else number / 20
    return round(min(max(number, 0), 5), 1)
