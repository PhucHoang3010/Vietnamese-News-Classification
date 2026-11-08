"""Bộ kiểm tra thiên vị (bias guard).

Quét nhận xét của AI và của người phỏng vấn để phát hiện nội dung dựa trên
thuộc tính được bảo vệ (giới tính, tuổi, hôn nhân/thai sản, vùng miền, tôn giáo,
ngoại hình, sức khoẻ). Nội dung bị gắn cờ cần người phụ trách kiểm duyệt.
"""
from __future__ import annotations

import re

PROTECTED_PATTERNS: dict[str, list[str]] = {
    "Giới tính": [r"nam giới", r"nữ giới", r"phụ nữ", r"đàn ông", r"con gái", r"con trai", r"\bnữ\b",
                  r"\bfemale\b", r"\bmale\b", r"giới tính", r"\bgender\b"],
    "Tuổi tác": [r"lớn tuổi", r"\bgià\b", r"còn trẻ", r"trẻ quá", r"quá trẻ", r"tuổi đời", r"\d{2}\s*tuổi",
                 r"độ tuổi", r"\bage\b", r"too old", r"too young"],
    "Hôn nhân / Thai sản": [r"kết hôn", r"lập gia đình", r"đã có gia đình", r"có con", r"con nhỏ", r"mang thai",
                            r"thai sản", r"sinh con", r"độc thân", r"\bmarried\b", r"pregnan", r"maternity"],
    "Vùng miền / Quê quán": [r"quê quán", r"\bquê\b", r"người miền (?:bắc|trung|nam|tây)", r"dân tỉnh",
                             r"người (?:bắc|nam|trung)\b", r"giọng (?:miền|bắc|nam|trung|địa phương|vùng)", r"miền (?:bắc|trung|nam|tây)\b",
                             r"hometown"],
    "Tôn giáo / Dân tộc": [r"tôn giáo", r"theo đạo", r"phật giáo", r"công giáo", r"dân tộc", r"religio"],
    "Ngoại hình": [r"ngoại hình", r"xinh", r"đẹp trai", r"\bbéo\b", r"\bmập\b", r"\bgầy\b", r"cao ráo",
                   r"appearance", r"attractive"],
    "Sức khoẻ / Khuyết tật": [r"khuyết tật", r"bệnh nền", r"sức khỏe yếu", r"sức khoẻ yếu", r"disabilit"],
}

_COMPILED = {cat: [re.compile(p, re.I) for p in pats] for cat, pats in PROTECTED_PATTERNS.items()}


def scan_text(text: str | None) -> list[dict]:
    """Trả về danh sách cờ: [{category, term, snippet}]."""
    if not text:
        return []
    flags = []
    seen: set[tuple[str, str]] = set()
    for category, patterns in _COMPILED.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                term = match.group(0).lower()
                if (category, term) in seen:
                    continue
                seen.add((category, term))
                start, end = max(match.start() - 40, 0), min(match.end() + 40, len(text))
                flags.append({"category": category, "term": term, "snippet": "…" + text[start:end].strip() + "…"})
    return flags


def scan_object(obj) -> list[dict]:
    """Quét đệ quy mọi chuỗi trong dict/list (nội dung JSON do AI sinh ra)."""
    texts: list[str] = []

    def walk(node):
        if isinstance(node, str):
            texts.append(node)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(obj)
    return scan_text("\n".join(texts))


FAIRNESS_GUIDELINES = [
    "AI chỉ tóm tắt và gợi ý; mọi quyết định tuyển dụng do con người đưa ra.",
    "Không dùng giới tính, tuổi, tình trạng hôn nhân, quê quán, tôn giáo, ngoại hình làm tiêu chí đánh giá.",
    "Thông tin cá nhân được ẩn trước khi gửi tới mô hình AI.",
    "Mọi nhận xét AI ở trạng thái 'Chờ duyệt' cho tới khi HR kiểm duyệt.",
    "Đánh giá phỏng vấn theo bộ câu hỏi có cấu trúc gắn với yêu cầu công việc.",
]
