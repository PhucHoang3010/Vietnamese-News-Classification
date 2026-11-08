"""TRANSFORM – đưa bản ghi thô của từng nguồn về một cấu trúc chuẩn (CanonicalApplication)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from app.etl.extract import CvLocator, RawItem
from app.etl.normalize import (
    clean_str,
    map_outcome,
    map_source,
    map_stage,
    map_status,
    normalize_city,
    normalize_education,
    normalize_email,
    normalize_gender,
    normalize_name,
    normalize_phone,
    parse_date,
    parse_datetime,
    parse_salary_million,
    parse_score,
    parse_years_experience,
)
from app.reference import STAGES
from app.utils import normalize_key, strip_accents

STAGE_ORDER = {code: order for code, _n, order, *_ in STAGES}


class TransformError(ValueError):
    """Bản ghi không hợp lệ, bị loại khỏi lần nạp."""


@dataclass
class CanonicalEvent:
    stage_code: str
    entered_at: datetime
    exited_at: datetime | None = None
    outcome: str | None = None
    interviewer: str | None = None
    score: float | None = None
    feedback: str | None = None


@dataclass
class CanonicalApplication:
    source_system: str
    source_file: str
    record_no: int
    external_id: str | None
    full_name: str | None
    email: str | None
    phone: str | None
    position_text: str | None
    source_code: str
    applied_at: datetime | None
    gender: str | None = None
    date_of_birth: date | None = None
    city: str | None = None
    years_experience: float | None = None
    education_level: str | None = None
    current_title: str | None = None
    skills_text: str | None = None
    cv_text: str | None = None
    cv_file_name: str | None = None
    expected_salary: float | None = None
    status: str | None = None
    closed_at: datetime | None = None
    rejection_reason: str | None = None
    events: list[CanonicalEvent] = field(default_factory=list)
    update_only: bool = False  # ví dụ email rút hồ sơ: chỉ cập nhật hồ sơ đã có
    warnings: list[str] = field(default_factory=list)


def pick(payload: dict[str, Any], *candidates: str) -> Any:
    """Lấy giá trị theo tên cột linh hoạt (so khớp tiêu đề sau khi bỏ dấu)."""
    normalized = {normalize_key(k): v for k, v in payload.items()}
    for cand in candidates:
        key = normalize_key(cand)
        if key in normalized and normalized[key] not in (None, ""):
            return normalized[key]
    for cand in candidates:
        key = normalize_key(cand)
        for header, value in normalized.items():
            if key and key in header and value not in (None, ""):
                return value
    return None


def _contact(rec: CanonicalApplication, raw_email: Any, raw_phone: Any) -> None:
    rec.email = normalize_email(raw_email)
    if raw_email and not rec.email:
        rec.warnings.append(f"email không hợp lệ '{raw_email}' → bỏ trống")
    rec.phone = normalize_phone(raw_phone)
    if raw_phone not in (None, "") and not rec.phone:
        rec.warnings.append(f"số điện thoại không hợp lệ '{raw_phone}' → bỏ trống")


def finalize_events(rec: CanonicalApplication) -> None:
    """Sắp xếp sự kiện theo thứ tự vòng, bổ sung kết quả & thời điểm rời vòng."""
    by_stage: dict[str, CanonicalEvent] = {}
    for ev in rec.events:
        if ev.entered_at is None:
            continue
        if ev.stage_code not in by_stage or ev.entered_at < by_stage[ev.stage_code].entered_at:
            by_stage[ev.stage_code] = ev
    if rec.applied_at and "APPLIED" not in by_stage and not rec.update_only:
        by_stage["APPLIED"] = CanonicalEvent("APPLIED", rec.applied_at)
    events = sorted(by_stage.values(), key=lambda e: STAGE_ORDER[e.stage_code])
    for i, ev in enumerate(events):
        is_last = i == len(events) - 1
        if not is_last:
            nxt = events[i + 1]
            if ev.exited_at is None:
                ev.exited_at = nxt.entered_at
            if ev.outcome in (None, "pending"):
                ev.outcome = "passed"
        else:
            if ev.stage_code == "HIRED":
                ev.outcome = ev.outcome or "passed"
            elif rec.status == "rejected":
                ev.outcome = ev.outcome if ev.outcome in ("failed", "no_show") else "failed"
            elif rec.status == "withdrawn":
                ev.outcome = "withdrawn"
            else:
                ev.outcome = ev.outcome or "pending"
            if ev.exited_at is None and rec.status in ("rejected", "withdrawn", "hired") and rec.closed_at:
                ev.exited_at = max(rec.closed_at, ev.entered_at)
    rec.events = events
    if events and events[-1].stage_code == "HIRED":
        rec.status = "hired"
        rec.closed_at = rec.closed_at or events[-1].entered_at


# --------------------------------------------------------------------------- #
# Từng nguồn
# --------------------------------------------------------------------------- #
def transform_google_form(item: RawItem, cvs: CvLocator) -> CanonicalApplication:
    p = item.payload
    rec = CanonicalApplication(
        source_system=item.source_system, source_file=item.source_file, record_no=item.record_no,
        external_id=None,
        full_name=normalize_name(pick(p, "Họ và tên", "Họ tên")),
        email=None, phone=None,
        position_text=clean_str(pick(p, "Vị trí ứng tuyển", "Vị trí")),
        source_code=map_source(pick(p, "biết đến tin tuyển dụng", "kênh", "nguồn")),
        applied_at=parse_datetime(pick(p, "Dấu thời gian", "Timestamp")),
        gender=normalize_gender(pick(p, "Giới tính")),
        date_of_birth=parse_date(pick(p, "Ngày sinh")),
        city=normalize_city(pick(p, "Tỉnh/Thành phố", "Thành phố", "Nơi ở")),
        years_experience=parse_years_experience(pick(p, "Số năm kinh nghiệm", "kinh nghiệm")),
        education_level=normalize_education(pick(p, "Trình độ học vấn", "Học vấn")),
        current_title=clean_str(pick(p, "Chức danh hiện tại", "Công việc hiện tại")),
        skills_text=clean_str(pick(p, "Kỹ năng nổi bật", "Kỹ năng")),
        expected_salary=parse_salary_million(pick(p, "Mức lương mong muốn", "lương")),
        status="active",
    )
    _contact(rec, pick(p, "Địa chỉ email", "Email"), pick(p, "Số điện thoại", "SĐT"))
    rec.cv_text, rec.cv_file_name = cvs.read(clean_str(pick(p, "Tải lên CV", "CV", "Link CV")))
    return rec


def transform_ats(item: RawItem, cvs: CvLocator) -> CanonicalApplication:
    p = item.payload
    cand = p.get("candidate", {})
    job = p.get("job", {})
    name = " ".join(x for x in [cand.get("last_name"), cand.get("first_name")] if x) or cand.get("name")
    rec = CanonicalApplication(
        source_system="ATS", source_file=item.source_file, record_no=item.record_no,
        external_id=p.get("id"),
        full_name=normalize_name(name), email=None, phone=None,
        position_text=job.get("req_id") or job.get("title"),
        source_code=map_source(p.get("source")),
        applied_at=parse_datetime(p.get("applied_at")),
        gender=normalize_gender(cand.get("gender")),
        date_of_birth=parse_date(cand.get("birth_date")),
        city=normalize_city(cand.get("location")),
        years_experience=parse_years_experience(cand.get("years_of_experience")),
        education_level=normalize_education(cand.get("education")),
        current_title=clean_str(cand.get("headline")),
        skills_text=", ".join(cand.get("tags", []) or []) or None,
        expected_salary=parse_salary_million(p.get("expected_salary")),
        status=map_status(p.get("status")) or "active",
        closed_at=parse_datetime(p.get("closed_at")),
        rejection_reason=clean_str(p.get("rejection_reason")),
    )
    emails = cand.get("emails") or []
    phones = cand.get("phones") or []
    _contact(rec, emails[0] if emails else None, phones[0] if phones else None)
    for st in p.get("stages", []):
        code = map_stage(st.get("name"))
        if not code:
            rec.warnings.append(f"không nhận diện được vòng '{st.get('name')}'")
            continue
        rec.events.append(CanonicalEvent(
            stage_code=code, entered_at=parse_datetime(st.get("entered_at")),
            exited_at=parse_datetime(st.get("exited_at")), outcome=map_outcome(st.get("result")),
            interviewer=clean_str(st.get("interviewer")), score=parse_score(st.get("score")),
            feedback=clean_str(st.get("notes")),
        ))
    rec.cv_text, rec.cv_file_name = cvs.read(cand.get("resume_file"))
    return rec


EXCEL_STAGE_COLUMNS = [
    ("APPLIED", ["Ngày nộp", "Ngày ứng tuyển"], None, None, None),
    ("SCREENING", ["Ngày duyệt CV", "Ngày sàng lọc"], None, None, None),
    ("HR_INTERVIEW", ["Ngày PV HR"], ["KQ PV HR", "Kết quả PV HR"], None, None),
    ("TECH_INTERVIEW", ["Ngày PV chuyên môn", "Ngày PV kỹ thuật"], ["KQ PV chuyên môn", "Kết quả PV chuyên môn"],
     ["Người PV chuyên môn"], ["Điểm PV", "Điểm"]),
    ("FINAL_INTERVIEW", ["Ngày PV cuối"], ["KQ PV cuối", "Kết quả PV cuối"], None, None),
    ("OFFER", ["Ngày gửi offer", "Ngày offer"], ["KQ offer", "Kết quả offer"], None, None),
    ("HIRED", ["Ngày nhận việc", "Ngày onboard"], None, None, None),
]


def transform_excel(item: RawItem, cvs: CvLocator) -> CanonicalApplication:
    p = item.payload
    rec = CanonicalApplication(
        source_system="EXCEL", source_file=item.source_file, record_no=item.record_no, external_id=None,
        full_name=normalize_name(pick(p, "Họ tên ứng viên", "Họ tên", "Họ và tên")),
        email=None, phone=None,
        position_text=clean_str(pick(p, "Vị trí", "Vị trí ứng tuyển")),
        source_code=map_source(pick(p, "Nguồn", "Kênh")),
        applied_at=parse_datetime(pick(p, "Ngày nộp", "Ngày ứng tuyển")),
        status=map_status(pick(p, "Trạng thái")) or "active",
        closed_at=parse_datetime(pick(p, "Ngày cập nhật")),
        rejection_reason=clean_str(pick(p, "Lý do loại/rút", "Lý do loại", "Lý do")),
    )
    _contact(rec, pick(p, "Email"), pick(p, "Số ĐT", "SĐT", "Điện thoại"))
    for code, date_cols, result_cols, interviewer_cols, score_cols in EXCEL_STAGE_COLUMNS:
        entered = parse_datetime(pick(p, *date_cols))
        if not entered:
            continue
        rec.events.append(CanonicalEvent(
            stage_code=code, entered_at=entered,
            outcome=map_outcome(pick(p, *result_cols)) if result_cols else None,
            interviewer=clean_str(pick(p, *interviewer_cols)) if interviewer_cols else None,
            score=parse_score(pick(p, *score_cols)) if score_cols else None,
            feedback=clean_str(pick(p, "Ghi chú")) if code == "TECH_INTERVIEW" else None,
        ))
    return rec


_WITHDRAW_KEYS = ["rut ho so", "xin rut", "khong tiep tuc", "huy ung tuyen", "tu choi offer", "khong tham gia"]


def transform_email(item: RawItem, cvs: CvLocator) -> CanonicalApplication:
    p = item.payload
    subject, body = p.get("subject") or "", p.get("body") or ""
    plain = normalize_key(subject + " " + body)
    is_withdraw = any(k in plain for k in _WITHDRAW_KEYS)

    name = p.get("from_name")
    m = re.search(r"(?:tên là|tên|Họ tên)\s*:?\s*([A-ZĐÀ-Ỹ][\wÀ-ỹ]*(?:\s+[A-ZĐÀ-Ỹ][\wÀ-ỹ]*){1,4})", body)
    if m:
        name = m.group(1)
    position = None
    m = re.search(r"\]\s*(.+?)\s+-\s+", subject) or re.search(r"vị trí\s+(.+?)(?:\s+-\s+|[,.\n]|$)", subject, re.I)
    if m:
        position = m.group(1)
    else:
        m = re.search(r"vị trí\s+(.+?)(?:\s+-\s+|[,.\n]| tại | vì |$)", body, re.I)
        position = m.group(1) if m else None
    phone = None
    m = re.search(r"(?:SĐT|Điện thoại|Phone|ĐT)\s*:?\s*([+\d][\d .\-]{8,15})", body, re.I)
    if m:
        phone = m.group(1)
    source_code = "DIRECT_EMAIL"
    m = re.search(r"(?:qua|trên|từ)\s+(?:kênh\s+|trang\s+|website\s+)?([\w.]+(?:\s[\w.]+)?)", body)
    if m and map_source(m.group(1)) != "OTHER":
        source_code = map_source(m.group(1))

    rec = CanonicalApplication(
        source_system="EMAIL", source_file=item.source_file, record_no=item.record_no,
        external_id=p.get("message_id"), full_name=normalize_name(name), email=None, phone=None,
        position_text=clean_str(position), source_code=source_code,
        applied_at=parse_datetime(p.get("date")),
    )
    _contact(rec, p.get("from_email"), phone)
    if is_withdraw:
        rec.update_only = True
        rec.status = "withdrawn"
        rec.closed_at = rec.applied_at
        m = re.search(r"\b(?:vì|do|lý do)\s+(.+?)(?:[.!\n]|$)", body, re.I)
        reason = clean_str(m.group(1)) if m else None
        rec.rejection_reason = (reason[0].upper() + reason[1:]) if reason else "Ứng viên gửi email rút hồ sơ"
    else:
        rec.status = "active"
        for att in p.get("attachments", []):
            if att.get("text"):
                rec.cv_text, rec.cv_file_name = att["text"], att["filename"]
                break
        if rec.cv_text:
            from app.ai.cv_parser import guess_education, guess_years_experience

            rec.years_experience = guess_years_experience(rec.cv_text)
            rec.education_level = guess_education(rec.cv_text)
    return rec


TRANSFORMERS = {
    "GOOGLE_FORM": transform_google_form,
    "ATS": transform_ats,
    "EXCEL": transform_excel,
    "EMAIL": transform_email,
}


def transform_item(item: RawItem, cvs: CvLocator) -> CanonicalApplication:
    rec = TRANSFORMERS[item.source_system](item, cvs)
    if not rec.full_name:
        raise TransformError("thiếu họ tên ứng viên")
    if not rec.email and not rec.phone:
        raise TransformError("thiếu thông tin liên hệ hợp lệ (email/SĐT) – không thể định danh")
    if not rec.position_text:
        raise TransformError("thiếu vị trí ứng tuyển")
    if not rec.applied_at and not rec.update_only:
        raise TransformError("thiếu hoặc sai định dạng ngày nộp hồ sơ")
    if rec.cv_text and rec.years_experience is None:
        from app.ai.cv_parser import guess_years_experience

        rec.years_experience = guess_years_experience(rec.cv_text)
    finalize_events(rec)
    return rec


def name_dob_key(name: str | None, dob: date | None) -> str | None:
    if not name or not dob:
        return None
    return f"{strip_accents(name).lower()}|{dob.isoformat()}"
