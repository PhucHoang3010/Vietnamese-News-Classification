"""Danh mục, danh sách hồ sơ ứng tuyển, chi tiết ứng viên và ghi nhận kết quả từng vòng."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.ai.bias_guard import scan_text
from app.ai.rejection import classify_reason
from app.ai.service import can_view_insight
from app.config import get_settings
from app.database import get_db
from app.models import AIInsight, Application, Candidate, Department, Position, Source, Stage, StageEvent, User
from app.rbac import ROLE_LABELS, get_current_user, has_perm, require
from app.schemas import StageDecision
from app.serializers import application_out, insight_out
from app.services.analytics import scoped_department
from app.services.audit import log_action
from app.utils import now_vn

router = APIRouter(tags=["Ứng viên & hồ sơ"])


@router.get("/meta")
def meta(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dept = scoped_department(user)
    positions = select(Position).order_by(Position.code)
    if dept is not None:
        positions = positions.where(Position.department_id == dept)
    settings = get_settings()
    return {
        "departments": [{"id": d.id, "code": d.code, "name": d.name} for d in db.scalars(select(Department))
                        if dept is None or d.id == dept],
        "positions": [{"id": p.id, "code": p.code, "title": p.title, "department_id": p.department_id,
                       "headcount": p.headcount, "required_skills": p.required_skills,
                       "nice_to_have_skills": p.nice_to_have_skills, "jd_text": p.jd_text, "location": p.location,
                       "level": p.level} for p in db.scalars(positions)],
        "sources": [{"id": s.id, "code": s.code, "name": s.name} for s in db.scalars(select(Source).order_by(Source.id))],
        "stages": [{"id": s.id, "code": s.code, "name": s.name, "order": s.stage_order, "sla_days": s.sla_days}
                   for s in db.scalars(select(Stage).order_by(Stage.stage_order))],
        "roles": ROLE_LABELS,
        "ai": {"provider": "claude" if settings.use_claude else "local",
               "model": settings.llm_model if settings.use_claude else "talentlens-nlp-rules-v1"},
    }


def _scoped_query(user: User):
    q = (select(Application).join(Position, Application.position_id == Position.id)
         .join(Candidate, Application.candidate_id == Candidate.id))
    dept = scoped_department(user)
    if dept is not None:
        q = q.where(Position.department_id == dept)
    return q


def get_application(db: Session, app_id: int, user: User) -> Application:
    app = db.scalar(_scoped_query(user).where(Application.id == app_id)
                    .options(selectinload(Application.events).selectinload(StageEvent.stage)))
    if app is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ hoặc bạn không có quyền xem")
    return app


@router.get("/applications")
def list_applications(
    q: str | None = None, position_id: int | None = None, department_id: int | None = None,
    stage: str | None = None, status: str | None = None, source_id: int | None = None,
    over_sla: bool = False, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=500),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = _scoped_query(user)
    if q:
        term = f"%{q.strip()}%"
        conds = [Candidate.candidate_code.ilike(term), Application.application_code.ilike(term)]
        if has_perm(user, "pii:read"):  # chỉ HR mới được tìm theo thông tin cá nhân
            conds += [Candidate.full_name.ilike(term), Candidate.email.ilike(term), Candidate.phone.ilike(term)]
        query = query.where(or_(*conds))
    if position_id:
        query = query.where(Application.position_id == position_id)
    if department_id:
        query = query.where(Position.department_id == department_id)
    if stage:
        query = query.join(Stage, Application.current_stage_id == Stage.id).where(Stage.code == stage)
    if status:
        query = query.where(Application.status == status)
    if source_id:
        query = query.where(Application.source_id == source_id)
    query = query.options(selectinload(Application.events).selectinload(StageEvent.stage),
                          selectinload(Application.candidate), selectinload(Application.position))
    rows = [application_out(a, user) for a in db.scalars(query.order_by(Application.applied_at.desc()))]
    if over_sla:
        rows = [r for r in rows if r["over_sla"]]
    total = len(rows)
    start = (page - 1) * page_size
    return {"total": total, "page": page, "page_size": page_size, "items": rows[start:start + page_size]}


@router.get("/applications/{app_id}")
def application_detail(app_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    app = get_application(db, app_id, user)
    data = application_out(app, user, full=True)
    insights = db.scalars(select(AIInsight).where(AIInsight.application_id == app.id)
                          .order_by(AIInsight.created_at.desc(), AIInsight.id.desc()))
    data["insights"] = [insight_out(i, user) for i in insights if can_view_insight(user, i)]
    others = db.scalars(select(Application).where(Application.candidate_id == app.candidate_id,
                                                  Application.id != app.id))
    data["other_applications"] = [{"id": o.id, "application_code": o.application_code, "position": o.position.title,
                                   "status": o.status} for o in others
                                  if scoped_department(user) in (None, o.position.department_id)]
    if has_perm(user, "pii:read"):
        log_action(db, user, "candidate:view_pii", "candidate", app.candidate_id)
        db.commit()
    return data


@router.post("/applications/{app_id}/decision")
def record_decision(app_id: int, body: StageDecision, db: Session = Depends(get_db),
                    user: User = Depends(require("feedback:write"))):
    """Ghi nhận kết quả vòng hiện tại: đạt → chuyển vòng kế tiếp; không đạt/rút/vắng → đóng hồ sơ."""
    app = get_application(db, app_id, user)
    if app.status != "active":
        raise HTTPException(status_code=400, detail="Hồ sơ đã đóng, không thể cập nhật vòng")
    flags = scan_text(" ".join(filter(None, [body.feedback, body.reason])))
    if flags and not body.force:
        raise HTTPException(status_code=422, detail={
            "message": "Nhận xét có nội dung liên quan đến thuộc tính được bảo vệ. Vui lòng sửa lại theo tiêu chí công "
                       "việc hoặc xác nhận lưu (sẽ được ghi nhận để kiểm duyệt).", "bias_flags": flags})
    stages = {s.code: s for s in db.scalars(select(Stage))}
    ordered = sorted(stages.values(), key=lambda s: s.stage_order)
    current = next(e for e in app.events if e.stage_id == app.current_stage_id)
    now = now_vn()
    current.exited_at = now
    current.duration_hours = round((now - current.entered_at).total_seconds() / 3600, 1)
    current.score = body.score if body.score is not None else current.score
    current.feedback = body.feedback or current.feedback
    current.interviewer = body.interviewer or current.interviewer or user.full_name
    current.bias_flags = flags
    if body.decision == "pass":
        current.outcome = "passed"
        nxt = next((s for s in ordered if s.stage_order == current.stage.stage_order + 1), None)
        if nxt is None:
            raise HTTPException(status_code=400, detail="Hồ sơ đã ở vòng cuối")
        db.add(StageEvent(application_id=app.id, stage_id=nxt.id, entered_at=now,
                          outcome="passed" if nxt.code == "HIRED" else "pending", source_system="WEB", bias_flags=[]))
        app.current_stage_id = nxt.id
        if nxt.code == "HIRED":
            app.status, app.closed_at = "hired", now
    else:
        current.outcome = {"fail": "failed", "withdraw": "withdrawn", "no_show": "no_show"}[body.decision]
        app.status = "withdrawn" if body.decision == "withdraw" else "rejected"
        app.closed_at = now
        app.rejection_reason = body.reason or body.feedback
        app.rejection_category = classify_reason(app.rejection_reason)
    log_action(db, user, f"application:{body.decision}", "application", app.id, stage=current.stage.code,
               bias_flags=len(flags))
    db.commit()
    db.expire_all()
    return application_out(get_application(db, app_id, user), user, full=True)


@router.get("/candidates/stats")
def candidate_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(func.count(func.distinct(Application.candidate_id))).join(Position)
    dept = scoped_department(user)
    if dept is not None:
        q = q.where(Position.department_id == dept)
    return {"candidates": db.scalar(q) or 0}
