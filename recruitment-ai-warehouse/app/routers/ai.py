"""API AI: tóm tắt CV, phân nhóm kỹ năng, câu hỏi phỏng vấn, lý do rớt, kiểm duyệt nhận xét AI."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import service
from app.ai.bias_guard import FAIRNESS_GUIDELINES
from app.database import get_db
from app.models import AIInsight, Position, User
from app.rbac import get_current_user, require
from app.routers.candidates import get_application
from app.schemas import InsightReview, RejectionInsightRequest
from app.serializers import insight_out
from app.services import analytics

router = APIRouter(prefix="/ai", tags=["AI / NLP"])
MAX_CV_BYTES = 5 * 1024 * 1024


@router.get("/guidelines")
def guidelines(_: User = Depends(get_current_user)):
    return {"guidelines": FAIRNESS_GUIDELINES}


@router.post("/applications/{app_id}/analyze-cv")
def analyze_cv(app_id: int, db: Session = Depends(get_db), user: User = Depends(require("ai:run"))):
    app = get_application(db, app_id, user)
    return insight_out(service.analyze_application_cv(db, app, user), user)


@router.post("/analyze-cv-file")
async def analyze_cv_file(file: UploadFile = File(...), position_id: int | None = Form(None),
                          db: Session = Depends(get_db), user: User = Depends(require("ai:run"))):
    data = await file.read()
    if len(data) > MAX_CV_BYTES:
        raise HTTPException(status_code=413, detail="File CV vượt quá 5MB")
    position = db.get(Position, position_id) if position_id else None
    return insight_out(service.analyze_uploaded_cv(db, data, file.filename or "cv.txt", position, user), user)


@router.post("/applications/{app_id}/interview-questions")
def interview_questions(app_id: int, db: Session = Depends(get_db), user: User = Depends(require("ai:run"))):
    app = get_application(db, app_id, user)
    return insight_out(service.interview_questions(db, app, user), user)


@router.post("/rejection-insights")
def rejection_insights(body: RejectionInsightRequest, db: Session = Depends(get_db),
                       user: User = Depends(require("ai:run"))):
    apps, _events = analytics.load_frames(
        db, user, analytics.Filters(department_id=body.department_id, position_id=body.position_id))
    stats = analytics.rejection_stats(apps)
    if not stats["total"]:
        raise HTTPException(status_code=400, detail="Chưa có hồ sơ bị loại/rút trong phạm vi đã chọn")
    return insight_out(service.rejection_insights(db, user, stats, body.position_id), user)


@router.get("/insights")
def list_insights(status: str | None = None, insight_type: str | None = None, application_id: int | None = None,
                  limit: int = 100, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(AIInsight).order_by(AIInsight.created_at.desc(), AIInsight.id.desc())
    if status:
        q = q.where(AIInsight.status == status)
    if insight_type:
        q = q.where(AIInsight.insight_type == insight_type)
    if application_id:
        q = q.where(AIInsight.application_id == application_id)
    rows = [i for i in db.scalars(q.limit(min(limit, 500))) if service.can_view_insight(user, i)]
    return [insight_out(i, user) for i in rows]


@router.get("/insights/{insight_id}")
def get_insight(insight_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    insight = db.get(AIInsight, insight_id)
    if insight is None or not service.can_view_insight(user, insight):
        raise HTTPException(status_code=404, detail="Không tìm thấy nhận xét AI")
    return insight_out(insight, user)


@router.post("/insights/{insight_id}/review")
def review_insight(insight_id: int, body: InsightReview, db: Session = Depends(get_db),
                   user: User = Depends(require("ai:review"))):
    insight = db.get(AIInsight, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhận xét AI")
    return insight_out(service.review(db, insight, user, body.action, body.note, body.edited_content), user)
