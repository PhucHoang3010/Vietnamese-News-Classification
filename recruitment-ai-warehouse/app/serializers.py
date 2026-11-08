"""Chuyển đối tượng ORM sang JSON, áp dụng che giấu dữ liệu theo quyền."""
from __future__ import annotations

from app.ai.anonymizer import anonymize_text
from app.ai.rejection import CATEGORY_LABELS
from app.models import AIInsight, Application, Candidate, StageEvent, User, WeeklyReport
from app.rbac import ROLE_LABELS, has_perm, initials, mask_email, mask_phone
from app.utils import now_vn

STATUS_LABELS = {"active": "Đang xử lý", "hired": "Đã nhận việc", "rejected": "Bị loại", "withdrawn": "Rút hồ sơ",
                 "on_hold": "Tạm dừng"}
OUTCOME_LABELS = {"passed": "Đạt", "failed": "Không đạt", "withdrawn": "Rút", "no_show": "Vắng mặt",
                  "pending": "Đang chờ"}
INSIGHT_LABELS = {"cv_analysis": "Tóm tắt CV", "interview_questions": "Câu hỏi phỏng vấn",
                  "rejection_insights": "Lý do rớt phổ biến"}
INSIGHT_STATUS = {"pending_review": "Chờ duyệt", "approved": "Đã duyệt", "rejected": "Đã từ chối"}


def iso(value):
    return value.isoformat() if value else None


def user_out(u: User) -> dict:
    return {"id": u.id, "username": u.username, "full_name": u.full_name, "email": u.email, "role": u.role,
            "role_label": ROLE_LABELS.get(u.role, u.role), "department_id": u.department_id,
            "department": u.department.name if u.department else None, "is_active": u.is_active,
            "created_at": iso(u.created_at), "last_login_at": iso(u.last_login_at)}


def candidate_out(c: Candidate, user: User, full: bool = False) -> dict:
    pii = has_perm(user, "pii:read")
    data = {
        "id": c.id, "candidate_code": c.candidate_code,
        "display_name": c.full_name if pii else f"{c.candidate_code} · {initials(c.full_name)}",
        "full_name": c.full_name if pii else None,
        "email": c.email if pii else mask_email(c.email),
        "phone": c.phone if pii else mask_phone(c.phone),
        "gender": c.gender if pii else None,
        "date_of_birth": iso(c.date_of_birth) if pii else None,
        "city": c.city if pii else None,
        "years_experience": c.years_experience, "education_level": c.education_level,
        "current_title": c.current_title, "skills": c.skills or [], "skill_groups": c.skill_groups or {},
        "has_cv": bool(c.cv_text), "pii_masked": not pii,
    }
    if full:
        data["cv_file_name"] = c.cv_file_name
        data["cv_text"] = c.cv_text if pii else anonymize_text(c.cv_text, [c.full_name])[0]
        data["merged_identities"] = (c.merged_identities or []) if pii else len(c.merged_identities or [])
    return data


def event_out(e: StageEvent) -> dict:
    return {"id": e.id, "stage": e.stage.code, "stage_name": e.stage.name, "stage_order": e.stage.stage_order,
            "entered_at": iso(e.entered_at), "exited_at": iso(e.exited_at), "outcome": e.outcome,
            "outcome_label": OUTCOME_LABELS.get(e.outcome, e.outcome),
            "duration_days": round(e.duration_hours / 24, 1) if e.duration_hours is not None else None,
            "interviewer": e.interviewer, "score": e.score, "feedback": e.feedback, "bias_flags": e.bias_flags or [],
            "source_system": e.source_system}


def application_out(a: Application, user: User, full: bool = False) -> dict:
    current = next((e for e in a.events if e.stage_id == a.current_stage_id), None)
    days = None
    if current and a.status == "active":
        days = round((now_vn() - current.entered_at).total_seconds() / 86400, 1)
    data = {
        "id": a.id, "application_code": a.application_code,
        "candidate": candidate_out(a.candidate, user, full=full),
        "position": {"id": a.position.id, "code": a.position.code, "title": a.position.title,
                     "department": a.position.department.name, "department_id": a.position.department_id},
        "source": a.source.name, "source_code": a.source.code,
        "applied_at": iso(a.applied_at), "status": a.status, "status_label": STATUS_LABELS.get(a.status, a.status),
        "current_stage": a.current_stage.code, "current_stage_name": a.current_stage.name,
        "current_stage_order": a.current_stage.stage_order,
        "days_in_current_stage": days, "sla_days": a.current_stage.sla_days,
        "over_sla": bool(days is not None and a.current_stage.sla_days and days > a.current_stage.sla_days),
        "closed_at": iso(a.closed_at), "rejection_reason": a.rejection_reason,
        "rejection_category": CATEGORY_LABELS.get(a.rejection_category) if a.rejection_category else None,
        "expected_salary": a.expected_salary,
    }
    if has_perm(user, "pii:read"):
        data["source_systems"] = a.source_systems or []
    if full:
        data["events"] = [event_out(e) for e in sorted(a.events, key=lambda e: e.stage.stage_order)]
    return data


def insight_out(i: AIInsight, user: User) -> dict:
    subject = None
    if i.candidate is not None:
        subject = candidate_out(i.candidate, user)["display_name"]
    elif i.insight_type == "cv_analysis":
        subject = i.content.get("file_name", "CV tải lên")
    return {"id": i.id, "insight_type": i.insight_type, "type_label": INSIGHT_LABELS.get(i.insight_type, i.insight_type),
            "subject": subject, "application_id": i.application_id,
            "application_code": i.application.application_code if i.application else None,
            "position": i.position.title if i.position else None, "content": i.content, "provider": i.provider,
            "model_name": i.model_name, "prompt_version": i.prompt_version, "status": i.status,
            "status_label": INSIGHT_STATUS.get(i.status, i.status), "bias_flags": i.bias_flags or [],
            "removed_fields": i.removed_fields or [], "edited": i.edited,
            "created_by": i.creator.full_name if i.creator else None, "created_at": iso(i.created_at),
            "reviewed_by": i.reviewer.full_name if i.reviewer else None, "reviewed_at": iso(i.reviewed_at),
            "review_note": i.review_note}


def report_out(r: WeeklyReport, include_body: bool = True) -> dict:
    data = {"id": r.id, "week_start": iso(r.week_start), "week_end": iso(r.week_end), "status": r.status,
            "status_label": "Đã duyệt" if r.status == "approved" else "Bản nháp", "provider": r.provider,
            "bias_flags": r.bias_flags or [], "created_by": r.creator.full_name if r.creator else None,
            "created_at": iso(r.created_at), "approved_by": r.approver.full_name if r.approver else None,
            "approved_at": iso(r.approved_at)}
    if include_body:
        data["narrative"] = r.narrative
        data["metrics"] = r.metrics
    return data
