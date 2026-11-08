"""Lớp dịch vụ AI: chọn engine (Claude / NLP nội bộ), ẩn danh dữ liệu, lưu kết quả chờ kiểm duyệt."""
from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.anonymizer import anonymize_text
from app.ai.bias_guard import scan_object
from app.ai.claude_engine import ClaudeEngine
from app.ai.cv_parser import extract_text
from app.ai.local_engine import LocalEngine
from app.config import get_settings
from app.models import AIInsight, Application, Candidate, Position, User
from app.rbac import has_perm
from app.services.audit import log_action
from app.utils import now_vn

logger = logging.getLogger("talentlens.ai")
NOT_SCANNED_KEYS = {"avoid_topics", "engine_note", "evidence_note", "scoring_guide", "anonymized_preview", "file_name"}
PROMPT_VERSION = "v1.2"


def get_engine():
    settings = get_settings()
    if settings.use_claude:
        return ClaudeEngine(settings.anthropic_api_key, settings.llm_model, settings.llm_effort,
                            settings.llm_timeout_seconds)
    return LocalEngine()


def call_engine(method: str, *args) -> tuple[dict, str, str, str | None]:
    """Gọi engine; nếu Claude lỗi thì tự chuyển sang engine nội bộ để hệ thống không gián đoạn."""
    engine = get_engine()
    try:
        return getattr(engine, method)(*args), engine.provider, engine.model_name, None
    except Exception as exc:  # noqa: BLE001
        if engine.provider == "local":
            raise
        logger.warning("Claude lỗi (%s) – chuyển sang engine nội bộ", exc)
        local = LocalEngine()
        return getattr(local, method)(*args), local.provider, local.model_name, f"Claude không khả dụng: {exc}"


def position_dict(pos: Position | None) -> dict | None:
    if pos is None:
        return None
    return {"id": pos.id, "code": pos.code, "title": pos.title, "department_code": pos.department.code,
            "required_skills": pos.required_skills or [], "nice_to_have_skills": pos.nice_to_have_skills or [],
            "jd_text": pos.jd_text or ""}


def _scan(content: dict) -> list[dict]:
    return scan_object({k: v for k, v in content.items() if k not in NOT_SCANNED_KEYS})


def _profile_text(cand: Candidate) -> str:
    return (f"Chức danh hiện tại: {cand.current_title or 'chưa rõ'}\nKINH NGHIỆM LÀM VIỆC\n"
            f"Tổng kinh nghiệm: {cand.years_experience if cand.years_experience is not None else 'chưa rõ'} năm\n"
            f"HỌC VẤN\n{cand.education_level or 'chưa rõ'}\nKỸ NĂNG\n{', '.join(cand.skills or [])}")


def _save(db: Session, user: User, insight_type: str, content: dict, provider: str, model: str, note: str | None,
          removed: list[str] | None = None, **links) -> AIInsight:
    if note:
        content["engine_note"] = note
    insight = AIInsight(insight_type=insight_type, content=content, provider=provider, model_name=model,
                        prompt_version=PROMPT_VERSION, status="pending_review", bias_flags=_scan(content),
                        removed_fields=removed or [], created_by=user.id, **links)
    db.add(insight)
    db.flush()
    log_action(db, user, f"ai:{insight_type}", "ai_insight", insight.id, provider=provider,
               bias_flags=len(insight.bias_flags))
    db.commit()
    db.refresh(insight)
    return insight


def analyze_application_cv(db: Session, app: Application, user: User) -> AIInsight:
    cand = app.candidate
    source_text = cand.cv_text or _profile_text(cand)
    text, removed = anonymize_text(source_text, names=[cand.full_name])
    context = {"years_experience": cand.years_experience, "education_level": cand.education_level,
               "current_title": cand.current_title, "skills_text": ", ".join(cand.skills or [])}
    content, provider, model, note = call_engine("analyze_cv", text, position_dict(app.position), context)
    content["has_cv_file"] = bool(cand.cv_text)
    content["anonymized_preview"] = text[:1500]
    return _save(db, user, "cv_analysis", content, provider, model, note, removed,
                 candidate_id=cand.id, application_id=app.id, position_id=app.position_id)


def analyze_uploaded_cv(db: Session, data: bytes, filename: str, position: Position | None, user: User) -> AIInsight:
    try:
        raw_text = extract_text(data, filename)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Không đọc được CV: {exc}") from exc
    if len(raw_text) < 30:
        raise HTTPException(status_code=400, detail="CV quá ngắn hoặc là ảnh scan chưa có lớp chữ (cần OCR)")
    first_line = next((l.strip() for l in raw_text.splitlines() if l.strip()), "")
    names = [first_line] if 1 < len(first_line.split()) <= 5 and not any(ch.isdigit() for ch in first_line) else []
    text, removed = anonymize_text(raw_text, names=names)
    content, provider, model, note = call_engine("analyze_cv", text, position_dict(position), {})
    content["has_cv_file"] = True
    content["file_name"] = filename
    content["anonymized_preview"] = text[:1500]
    return _save(db, user, "cv_analysis", content, provider, model, note, removed,
                 position_id=position.id if position else None)


def latest_insight(db: Session, application_id: int, insight_type: str) -> AIInsight | None:
    return db.scalar(select(AIInsight).where(AIInsight.application_id == application_id,
                                             AIInsight.insight_type == insight_type,
                                             AIInsight.status != "rejected")
                     .order_by(AIInsight.created_at.desc(), AIInsight.id.desc()))


def interview_questions(db: Session, app: Application, user: User) -> AIInsight:
    analysis = latest_insight(db, app.id, "cv_analysis")
    if analysis is None:
        analysis = analyze_application_cv(db, app, user)
    content, provider, model, note = call_engine("interview_questions", position_dict(app.position), analysis.content)
    return _save(db, user, "interview_questions", content, provider, model, note,
                 candidate_id=app.candidate_id, application_id=app.id, position_id=app.position_id)


def rejection_insights(db: Session, user: User, stats: dict, position_id: int | None = None) -> AIInsight:
    content, provider, model, note = call_engine("rejection_insights", stats)
    content["total"] = stats.get("total")
    content["withdrawn"] = stats.get("withdrawn")
    return _save(db, user, "rejection_insights", content, provider, model, note, position_id=position_id)


def review(db: Session, insight: AIInsight, user: User, action: str, note: str | None,
           edited_content: dict | None) -> AIInsight:
    if insight.status != "pending_review" and action != "reopen":
        raise HTTPException(status_code=400, detail="Nhận xét này đã được kiểm duyệt")
    if edited_content is not None:
        insight.content = edited_content
        insight.bias_flags = _scan(edited_content)
        insight.edited = True
    if action == "approve":
        if insight.bias_flags and not (note or "").strip():
            raise HTTPException(status_code=400,
                                detail="Nội dung có cờ thiên vị – cần chỉnh sửa hoặc ghi chú lý do trước khi duyệt")
        insight.status = "approved"
    elif action == "reject":
        insight.status = "rejected"
    elif action == "reopen":
        insight.status = "pending_review"
    else:
        raise HTTPException(status_code=400, detail="Hành động không hợp lệ")
    insight.reviewed_by = user.id
    insight.reviewed_at = now_vn()
    insight.review_note = note
    log_action(db, user, f"ai:review:{action}", "ai_insight", insight.id, edited=edited_content is not None)
    db.commit()
    db.refresh(insight)
    return insight


def can_view_insight(user: User, insight: AIInsight) -> bool:
    if has_perm(user, "ai:read_all"):
        return True
    if insight.status != "approved":
        return False
    if insight.position is None:
        return insight.insight_type == "rejection_insights"
    return insight.position.department_id == user.department_id
