"""API báo cáo pipeline tuần."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, WeeklyReport
from app.rbac import get_current_user, has_perm, require
from app.schemas import WeeklyReportRequest
from app.serializers import report_out
from app.services import reports
from app.services.audit import log_action
from app.utils import now_vn

router = APIRouter(prefix="/reports", tags=["Báo cáo tuần"])


def _visible(user: User, report: WeeklyReport) -> bool:
    return has_perm(user, "reports:generate") or report.status == "approved"


@router.post("/weekly")
def generate_weekly(body: WeeklyReportRequest, db: Session = Depends(get_db),
                    user: User = Depends(require("reports:generate"))):
    return report_out(reports.generate(db, user, body.week_start))


@router.get("")
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(WeeklyReport).order_by(WeeklyReport.week_start.desc(), WeeklyReport.id.desc()))
    return [report_out(r, include_body=False) for r in rows if _visible(user, r)]


def _get(db: Session, report_id: int, user: User) -> WeeklyReport:
    report = db.get(WeeklyReport, report_id)
    if report is None or not _visible(user, report):
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")
    return report


@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return report_out(_get(db, report_id, user))


@router.post("/{report_id}/approve")
def approve(report_id: int, db: Session = Depends(get_db), user: User = Depends(require("reports:approve"))):
    report = _get(db, report_id, user)
    report.status, report.approved_by, report.approved_at = "approved", user.id, now_vn()
    narrative = (report.metrics or {}).get("narrative", {})
    report.narrative = reports.render_markdown(report.metrics, narrative, approved_by=user.full_name)
    log_action(db, user, "report:approve", "weekly_report", report.id)
    db.commit()
    db.refresh(report)
    return report_out(report)


@router.get("/{report_id}/download")
def download(report_id: int, format: str = "md", db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    report = _get(db, report_id, user)
    filename = f"bao_cao_tuan_{report.week_start:%Y%m%d}"
    if format == "html":
        return HTMLResponse(reports.to_html(report),
                            headers={"Content-Disposition": f'attachment; filename="{filename}.html"'})
    return PlainTextResponse(report.narrative, media_type="text/markdown; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="{filename}.md"'})
