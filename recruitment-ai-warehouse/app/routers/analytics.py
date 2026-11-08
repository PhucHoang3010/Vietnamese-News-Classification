"""API phân tích pipeline & giám sát công bằng."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.rbac import get_current_user, require
from app.services import analytics

router = APIRouter(prefix="/analytics", tags=["Phân tích pipeline"])


def _filters(date_from: date | None = None, date_to: date | None = None, department_id: int | None = None,
             position_id: int | None = None, source_id: int | None = None) -> analytics.Filters:
    return analytics.Filters(date_from, date_to, department_id, position_id, source_id)


@router.get("/dashboard")
def dashboard(filters: analytics.Filters = Depends(_filters), db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    data = analytics.dashboard(db, user, filters)
    data["scope"] = "Toàn công ty" if analytics.scoped_department(user) is None else (
        user.department.name if user.department else "Phòng ban của bạn")
    return data


@router.get("/flagged-feedback")
def flagged_feedback(db: Session = Depends(get_db), user: User = Depends(require("fairness:read"))):
    """Nhận xét phỏng vấn (của con người) bị bộ lọc thiên vị gắn cờ."""
    from sqlalchemy import select

    from app.models import Application, StageEvent
    from app.serializers import iso

    rows = db.scalars(select(StageEvent).join(Application).order_by(StageEvent.entered_at.desc()))
    return [{"application_id": e.application_id, "application_code": e.application.application_code,
             "position": e.application.position.title, "stage": e.stage.name, "interviewer": e.interviewer,
             "entered_at": iso(e.entered_at), "feedback": e.feedback,
             "categories": sorted({f["category"] for f in e.bias_flags})}
            for e in rows if e.bias_flags]


@router.get("/fairness")
def fairness(filters: analytics.Filters = Depends(_filters), db: Session = Depends(get_db),
             user: User = Depends(require("fairness:read"))):
    apps, events = analytics.load_frames(db, user, filters, with_gender=True)
    return analytics.fairness(apps, events)
