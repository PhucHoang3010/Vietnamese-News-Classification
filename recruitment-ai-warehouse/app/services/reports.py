"""Báo cáo pipeline tuyển dụng hàng tuần (số liệu + nhận định AI), xuất Markdown/HTML."""
from __future__ import annotations

import html
from datetime import date, datetime, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from app.ai.bias_guard import scan_object
from app.ai.rejection import CATEGORY_LABELS
from app.ai.service import call_engine
from app.models import User, WeeklyReport
from app.services import analytics
from app.services.audit import log_action


def week_bounds(week_start: date) -> tuple[datetime, datetime]:
    start = datetime.combine(week_start - timedelta(days=week_start.weekday()), datetime.min.time())
    return start, start + timedelta(days=7)


def _week_metrics(apps: pd.DataFrame, events: pd.DataFrame, start: datetime, end: datetime) -> dict:
    if apps.empty:
        return {"new_applications": 0}
    new = apps[(apps.applied_at >= start) & (apps.applied_at < end)]
    ev = events[(events.entered_at >= start) & (events.entered_at < end)] if not events.empty else events
    closed = apps[(apps.closed_at >= start) & (apps.closed_at < end)]
    reasons = closed[closed.status.isin(["rejected", "withdrawn"])].rejection_category.dropna()
    return {
        "new_applications": int(len(new)),
        "interviews": int(ev.stage.isin(["HR_INTERVIEW", "TECH_INTERVIEW", "FINAL_INTERVIEW"]).sum()) if len(ev) else 0,
        "offers": int((ev.stage == "OFFER").sum()) if len(ev) else 0,
        "hires": int((ev.stage == "HIRED").sum()) if len(ev) else 0,
        "rejected": int((closed.status == "rejected").sum()),
        "withdrawn": int((closed.status == "withdrawn").sum()),
        "top_source": new.source.value_counts().index[0] if len(new) else None,
        "top_position": new.position.value_counts().index[0] if len(new) else None,
        "top_rejection_reason": CATEGORY_LABELS.get(reasons.value_counts().index[0]) if len(reasons) else None,
        "by_source": {k: int(v) for k, v in new.source.value_counts().items()},
        "by_position": {k: int(v) for k, v in new.position.value_counts().items()},
    }


def build_metrics(db: Session, user: User, week_start: date) -> dict:
    start, end = week_bounds(week_start)
    apps, events = analytics.load_frames(db, user)
    current = _week_metrics(apps, events, start, end)
    previous = _week_metrics(apps, events, start - timedelta(days=7), start)
    as_of_apps = apps[apps.applied_at < end] if not apps.empty else apps
    as_of_events = events[events.entered_at < end] if not events.empty else events
    current["stuck_applications"] = len(analytics.stuck_applications(as_of_apps, as_of_events))
    return {
        "week_start": start.date().isoformat(), "week_end": (end - timedelta(days=1)).date().isoformat(),
        "week_label": f"{start:%d/%m} – {(end - timedelta(days=1)):%d/%m/%Y}",
        "current": current, "previous": previous,
        "kpis_to_date": analytics.kpis(as_of_apps, as_of_events),
        "funnel_to_date": analytics.funnel(as_of_apps, as_of_events),
        "bottlenecks": analytics.bottlenecks(as_of_apps, as_of_events),
    }


def generate(db: Session, user: User, week_start: date) -> WeeklyReport:
    metrics = build_metrics(db, user, week_start)
    narrative, provider, _model, note = call_engine("weekly_narrative", metrics)
    if note:
        narrative["engine_note"] = note
    report = WeeklyReport(week_start=date.fromisoformat(metrics["week_start"]),
                          week_end=date.fromisoformat(metrics["week_end"]), metrics=metrics,
                          narrative=render_markdown(metrics, narrative), provider=provider, status="draft",
                          bias_flags=scan_object({k: v for k, v in narrative.items() if k != "engine_note"}),
                          created_by=user.id)
    report.metrics = {**metrics, "narrative": narrative}
    db.add(report)
    db.flush()
    log_action(db, user, "report:generate", "weekly_report", report.id, week=metrics["week_label"], provider=provider)
    db.commit()
    db.refresh(report)
    return report


def _delta(cur: int, prev: int) -> str:
    if not prev:
        return "–"
    change = (cur - prev) / prev * 100
    return f"{'+' if change >= 0 else ''}{change:.0f}%"


def render_markdown(metrics: dict, narrative: dict, approved_by: str | None = None) -> str:
    cur, prev = metrics["current"], metrics["previous"]
    rows = [("Hồ sơ mới", "new_applications"), ("Lượt phỏng vấn", "interviews"), ("Offer đã gửi", "offers"),
            ("Nhận việc", "hires"), ("Bị loại", "rejected"), ("Ứng viên rút hồ sơ", "withdrawn")]
    lines = [f"# Báo cáo pipeline tuyển dụng tuần {metrics['week_label']}", "",
             "## 1. Tóm tắt", narrative.get("summary", ""), "",
             "## 2. Chỉ số chính", "", "| Chỉ số | Tuần này | Tuần trước | Thay đổi |", "|---|---:|---:|---:|"]
    for label, key in rows:
        lines.append(f"| {label} | {cur.get(key, 0)} | {prev.get(key, 0)} | {_delta(cur.get(key, 0), prev.get(key, 0))} |")
    lines.append(f"| Hồ sơ quá hạn SLA (cuối tuần) | {cur.get('stuck_applications', 0)} | | |")
    k = metrics.get("kpis_to_date", {})
    lines += ["", f"Luỹ kế: {k.get('total_applications', 0)} hồ sơ, {k.get('hired', 0)} nhận việc, tỷ lệ tuyển "
                  f"{k.get('hire_rate_pct') or 0}%, thời gian tuyển trung bình {k.get('avg_time_to_hire_days') or '–'} ngày.",
              "", "## 3. Điểm nổi bật"] + [f"- {h}" for h in narrative.get("highlights", [])]
    lines += ["", "## 4. Rủi ro & điểm nghẽn"] + [f"- {r}" for r in narrative.get("risks", [])]
    lines += ["", "## 5. Hành động đề xuất"] + [f"- {a}" for a in narrative.get("actions", [])]
    if cur.get("by_source"):
        lines += ["", "## 6. Hồ sơ mới theo nguồn", "", "| Nguồn | Số hồ sơ |", "|---|---:|"]
        lines += [f"| {s} | {n} |" for s, n in cur["by_source"].items()]
    lines += ["", "---", "_Báo cáo được tạo tự động bởi TalentLens. Phần nhận định do AI hỗ trợ và "
                     + (f"đã được {approved_by} kiểm duyệt._" if approved_by else "đang chờ HR kiểm duyệt._")]
    return "\n".join(lines)


def to_html(report: WeeklyReport) -> str:
    body = []
    in_table = False
    for line in report.narrative.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-:"):
                continue
            if not in_table:
                body.append("<table>")
                in_table = True
                body.append("<tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cells) + "</tr>")
            else:
                body.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            body.append("</table>")
            in_table = False
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.strip() == "---":
            body.append("<hr>")
        elif line.strip():
            body.append(f"<p>{html.escape(line.strip('_'))}</p>")
    if in_table:
        body.append("</table>")
    style = ("body{font-family:Arial,sans-serif;max-width:860px;margin:32px auto;color:#1f2937;line-height:1.5}"
             "h1{color:#1e3a8a}table{border-collapse:collapse;width:100%}td,th{border:1px solid #d1d5db;"
             "padding:6px 10px;text-align:left}th{background:#eef2ff}")
    return (f"<!doctype html><html lang='vi'><head><meta charset='utf-8'><title>Báo cáo tuần</title>"
            f"<style>{style}</style></head><body>{''.join(body)}</body></html>")
