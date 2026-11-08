"""Phân tích pipeline tuyển dụng: phễu, tỷ lệ chuyển đổi, thời gian xử lý, điểm nghẽn, nguồn, công bằng.

Dữ liệu được lọc theo quyền của người dùng (hiring manager chỉ thấy phòng ban của mình).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.rejection import CATEGORY_LABELS
from app.models import Application, Candidate, Department, Position, Source, Stage, StageEvent, User
from app.rbac import has_perm
from app.utils import now_vn

PIPELINE = ["APPLIED", "SCREENING", "HR_INTERVIEW", "TECH_INTERVIEW", "FINAL_INTERVIEW", "OFFER", "HIRED"]
SHORT_NAMES = {"APPLIED": "Nộp hồ sơ", "SCREENING": "Sàng lọc", "HR_INTERVIEW": "PV HR",
               "TECH_INTERVIEW": "PV chuyên môn", "FINAL_INTERVIEW": "PV cuối", "OFFER": "Offer", "HIRED": "Nhận việc"}


@dataclass
class Filters:
    date_from: date | None = None
    date_to: date | None = None
    department_id: int | None = None
    position_id: int | None = None
    source_id: int | None = None


def scoped_department(user: User) -> int | None:
    """Phòng ban mà người dùng bị giới hạn (None = xem toàn bộ)."""
    if has_perm(user, "candidates:read_all"):
        return None
    return user.department_id or -1


def load_frames(db: Session, user: User, filters: Filters | None = None,
                with_gender: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    filters = filters or Filters()
    cols = [Application.id, Application.application_code, Application.candidate_id, Application.position_id,
            Position.title.label("position"), Position.code.label("position_code"), Position.headcount,
            Position.department_id, Department.code.label("department_code"), Department.name.label("department"),
            Application.source_id, Source.name.label("source"), Source.code.label("source_code"),
            Application.applied_at, Application.status, Application.closed_at, Stage.code.label("current_stage"),
            Application.rejection_reason, Application.rejection_category, Application.expected_salary]
    if with_gender:
        cols.append(Candidate.gender)
    q = (select(*cols).join(Position, Application.position_id == Position.id)
         .join(Department, Position.department_id == Department.id)
         .join(Source, Application.source_id == Source.id)
         .join(Stage, Application.current_stage_id == Stage.id))
    if with_gender:
        q = q.join(Candidate, Application.candidate_id == Candidate.id)
    dept = scoped_department(user)
    if dept is not None:
        q = q.where(Position.department_id == dept)
    if filters.department_id:
        q = q.where(Position.department_id == filters.department_id)
    if filters.position_id:
        q = q.where(Application.position_id == filters.position_id)
    if filters.source_id:
        q = q.where(Application.source_id == filters.source_id)
    if filters.date_from:
        q = q.where(Application.applied_at >= datetime.combine(filters.date_from, datetime.min.time()))
    if filters.date_to:
        q = q.where(Application.applied_at < datetime.combine(filters.date_to + timedelta(days=1), datetime.min.time()))
    apps = pd.DataFrame(db.execute(q).mappings().all())
    if apps.empty:
        return apps, pd.DataFrame(columns=["application_id", "stage", "stage_order", "entered_at", "exited_at",
                                           "outcome", "duration_hours", "sla_days"])
    eq = (select(StageEvent.application_id, Stage.code.label("stage"), Stage.stage_order, Stage.sla_days,
                 StageEvent.entered_at, StageEvent.exited_at, StageEvent.outcome, StageEvent.duration_hours,
                 StageEvent.score)
          .join(Stage, StageEvent.stage_id == Stage.id)
          .where(StageEvent.application_id.in_(apps["id"].tolist())))
    events = pd.DataFrame(db.execute(eq).mappings().all())
    return apps, events


def _pct(a: float, b: float) -> float | None:
    return round(a / b * 100, 1) if b else None


# --------------------------------------------------------------------------- #
def kpis(apps: pd.DataFrame, events: pd.DataFrame) -> dict:
    if apps.empty:
        return {"total_applications": 0}
    now = now_vn()
    hired = apps[apps.status == "hired"]
    tth = (hired.closed_at - hired.applied_at).dt.total_seconds() / 86400 if not hired.empty else pd.Series(dtype=float)
    offers = events[events.stage == "OFFER"]
    decided_offers = offers[offers.outcome.isin(["passed", "withdrawn", "failed"])]
    return {
        "total_applications": int(len(apps)),
        "unique_candidates": int(apps.candidate_id.nunique()),
        "active": int((apps.status == "active").sum()),
        "hired": int(len(hired)),
        "rejected": int((apps.status == "rejected").sum()),
        "withdrawn": int((apps.status == "withdrawn").sum()),
        "hire_rate_pct": _pct(len(hired), len(apps)),
        "avg_time_to_hire_days": round(float(tth.mean()), 1) if len(tth) else None,
        "median_time_to_hire_days": round(float(tth.median()), 1) if len(tth) else None,
        "offer_acceptance_pct": _pct((decided_offers.outcome == "passed").sum(), len(decided_offers)),
        "new_last_7_days": int((apps.applied_at >= now - timedelta(days=7)).sum()),
        "open_positions": int(apps.position_id.nunique()),
    }


def funnel(apps: pd.DataFrame, events: pd.DataFrame) -> list[dict]:
    if events.empty:
        return []
    start = apps.id.nunique()
    rows = []
    reached_prev = None
    for code in PIPELINE:
        ev = events[events.stage == code]
        reached = int(ev.application_id.nunique())
        rows.append({
            "stage": code, "stage_name": SHORT_NAMES[code], "reached": reached,
            "conversion_from_prev_pct": _pct(reached, reached_prev) if reached_prev is not None else 100.0,
            "conversion_from_start_pct": _pct(reached, start),
            "failed": int((ev.outcome.isin(["failed", "no_show"])).sum()),
            "withdrawn": int((ev.outcome == "withdrawn").sum()),
            "in_progress": int((ev.outcome == "pending").sum()),
        })
        reached_prev = reached
    for i, row in enumerate(rows[:-1]):
        nxt = rows[i + 1]["reached"]
        decided = nxt + row["failed"] + row["withdrawn"]
        row["pass_rate_pct"] = _pct(nxt, decided)  # tỷ lệ qua vòng trên số hồ sơ đã có kết quả
        row["dropoff"] = row["reached"] - nxt
    rows[-1]["pass_rate_pct"] = None
    rows[-1]["dropoff"] = 0
    return rows


def stage_durations(events: pd.DataFrame) -> list[dict]:
    """Thời gian chuyển vòng: từ khi vào vòng đến khi chuyển sang vòng kế tiếp (chỉ hồ sơ đi tiếp)."""
    if events.empty:
        return []
    rows = []
    for i, code in enumerate(PIPELINE[:-1]):
        ev = events[(events.stage == code) & (events.outcome == "passed") & events.duration_hours.notna()]
        days = ev.duration_hours / 24
        sla = int(events[events.stage == code].sla_days.iloc[0]) if (events.stage == code).any() else None
        rows.append({
            "stage": code, "transition": f"{SHORT_NAMES[code]} → {SHORT_NAMES[PIPELINE[i + 1]]}",
            "n": int(len(ev)), "avg_days": round(float(days.mean()), 1) if len(ev) else None,
            "median_days": round(float(days.median()), 1) if len(ev) else None,
            "p90_days": round(float(days.quantile(0.9)), 1) if len(ev) else None,
            "sla_days": sla, "over_sla_pct": _pct(int((days > sla).sum()), len(ev)) if sla and len(ev) else None,
        })
    return rows


def stuck_applications(apps: pd.DataFrame, events: pd.DataFrame, now: datetime | None = None) -> list[dict]:
    """Hồ sơ đang xử lý nhưng đã quá SLA ở vòng hiện tại (tính tại thời điểm `now`)."""
    if apps.empty or events.empty:
        return []
    now = now or now_vn()
    active = apps[apps.status == "active"][["id", "application_code", "position", "current_stage"]]
    cur = events.merge(active, left_on=["application_id", "stage"], right_on=["id", "current_stage"])
    cur = cur.assign(days_in_stage=(now - cur.entered_at).dt.total_seconds() / 86400)
    stuck = cur[cur.days_in_stage > cur.sla_days]
    return [{"application_code": r.application_code, "position": r.position, "stage": r.stage,
             "stage_name": SHORT_NAMES[r.stage], "days_in_stage": round(float(r.days_in_stage), 1),
             "sla_days": int(r.sla_days)} for r in stuck.sort_values("days_in_stage", ascending=False).itertuples()]


def bottlenecks(apps: pd.DataFrame, events: pd.DataFrame, now: datetime | None = None) -> list[dict]:
    result = []
    fn = [r for r in funnel(apps, events) if r.get("pass_rate_pct") is not None and r["reached"] >= 10]
    if fn:
        worst = min(fn, key=lambda r: r["pass_rate_pct"])
        result.append({"type": "conversion", "stage": worst["stage"], "value": worst["pass_rate_pct"],
                       "severity": "high" if worst["pass_rate_pct"] < 50 else "medium",
                       "message": f"Tỷ lệ qua vòng {worst['stage_name']} thấp nhất: {worst['pass_rate_pct']}% "
                                  f"({worst['dropoff']} hồ sơ dừng lại ở vòng này)."})
    durations = [d for d in stage_durations(events) if d["median_days"] is not None and d["n"] >= 5 and d["sla_days"]]
    if durations:
        slow = max(durations, key=lambda d: d["median_days"] / d["sla_days"])
        result.append({"type": "duration", "stage": slow["stage"], "value": slow["median_days"],
                       "severity": "high" if slow["median_days"] > slow["sla_days"] else "medium",
                       "message": f"Chuyển vòng chậm nhất: {slow['transition']} mất trung vị {slow['median_days']} ngày "
                                  f"(SLA {slow['sla_days']} ngày, {slow['over_sla_pct']}% hồ sơ vượt SLA)."})
    stuck = stuck_applications(apps, events, now)
    if stuck:
        by_stage = pd.Series([s["stage"] for s in stuck]).value_counts()
        stage = by_stage.index[0]
        result.append({"type": "aging", "stage": stage, "value": int(by_stage.iloc[0]), "severity": "medium",
                       "message": f"{len(stuck)} hồ sơ đang quá hạn SLA, nhiều nhất ở vòng {SHORT_NAMES[stage]} "
                                  f"({int(by_stage.iloc[0])} hồ sơ)."})
    if not apps.empty:
        withdrawn = apps[apps.status == "withdrawn"]
        if len(withdrawn) >= 5:
            stage = withdrawn.current_stage.value_counts().index[0]
            result.append({"type": "withdrawal", "stage": stage, "value": int(len(withdrawn)), "severity": "medium",
                           "message": f"{len(withdrawn)} ứng viên tự rút hồ sơ, tập trung ở vòng {SHORT_NAMES[stage]} – "
                                      f"cần rút ngắn thời gian chờ."})
    return result


def source_performance(apps: pd.DataFrame, events: pd.DataFrame) -> list[dict]:
    if apps.empty:
        return []
    reached = events.groupby("stage").application_id.apply(set).to_dict() if not events.empty else {}
    rows = []
    for (code, name), grp in apps.groupby(["source_code", "source"]):
        ids = set(grp.id)
        hired = grp[grp.status == "hired"]
        tth = (hired.closed_at - hired.applied_at).dt.total_seconds() / 86400
        rows.append({
            "source_code": code, "source": name, "applications": len(grp),
            "passed_screening_pct": _pct(len(ids & reached.get("HR_INTERVIEW", set())), len(grp)),
            "reached_tech_pct": _pct(len(ids & reached.get("TECH_INTERVIEW", set())), len(grp)),
            "offers": len(ids & reached.get("OFFER", set())), "hires": int(len(hired)),
            "hire_rate_pct": _pct(len(hired), len(grp)),
            "avg_time_to_hire_days": round(float(tth.mean()), 1) if len(hired) else None,
        })
    return sorted(rows, key=lambda r: r["applications"], reverse=True)


def weekly_trend(apps: pd.DataFrame, events: pd.DataFrame) -> list[dict]:
    if apps.empty:
        return []
    week = lambda s: (s.dt.normalize() - pd.to_timedelta(s.dt.weekday, unit="D")).dt.date  # noqa: E731
    applied = apps.assign(week=week(apps.applied_at)).groupby("week").size()
    closed = apps[apps.closed_at.notna()].assign(week=lambda d: week(d.closed_at))
    hires = closed[closed.status == "hired"].groupby("week").size()
    rejected = closed[closed.status == "rejected"].groupby("week").size()
    withdrawn = closed[closed.status == "withdrawn"].groupby("week").size()
    interviews = pd.Series(dtype=int)
    if not events.empty:
        iv = events[events.stage.isin(["HR_INTERVIEW", "TECH_INTERVIEW", "FINAL_INTERVIEW"])]
        interviews = iv.assign(week=week(iv.entered_at)).groupby("week").size()
    weeks = sorted(set(applied.index) | set(hires.index) | set(interviews.index))
    return [{"week_start": w.isoformat(), "applications": int(applied.get(w, 0)), "interviews": int(interviews.get(w, 0)),
             "hires": int(hires.get(w, 0)), "rejected": int(rejected.get(w, 0)), "withdrawn": int(withdrawn.get(w, 0))}
            for w in weeks]


def position_pipeline(apps: pd.DataFrame) -> list[dict]:
    if apps.empty:
        return []
    rows = []
    for (pid, title, code, dept), grp in apps.groupby(["position_id", "position", "position_code", "department"]):
        active = grp[grp.status == "active"].current_stage.value_counts().to_dict()
        rows.append({"position_id": int(pid), "position": title, "position_code": code, "department": dept,
                     "headcount": int(grp.headcount.iloc[0]), "applications": len(grp),
                     "hired": int((grp.status == "hired").sum()),
                     "active_by_stage": {SHORT_NAMES[k]: int(v) for k, v in active.items()},
                     "active": int((grp.status == "active").sum())})
    return sorted(rows, key=lambda r: r["applications"], reverse=True)


def rejection_stats(apps: pd.DataFrame) -> dict:
    closed = apps[apps.status.isin(["rejected", "withdrawn"])] if not apps.empty else apps
    if closed.empty:
        return {"total": 0, "withdrawn": 0, "categories": []}
    cats = []
    for code, grp in closed.groupby(closed.rejection_category.fillna("OTHER")):
        stages = grp.current_stage.value_counts()
        examples = grp.rejection_reason.dropna().value_counts().index.tolist()[:3]
        cats.append({"category": code, "label": CATEGORY_LABELS.get(code, code), "count": int(len(grp)),
                     "share_pct": _pct(len(grp), len(closed)),
                     "withdrawn": int((grp.status == "withdrawn").sum()),
                     "main_stages": [SHORT_NAMES[s] for s in stages.index[:2]], "examples": examples})
    cats.sort(key=lambda c: c["count"], reverse=True)
    by_stage = closed.groupby(["current_stage", closed.rejection_category.fillna("OTHER")]).size()
    matrix = [{"stage": SHORT_NAMES[s], "category": CATEGORY_LABELS.get(c, c), "count": int(n)}
              for (s, c), n in by_stage.items()]
    return {"total": int(len(closed)), "withdrawn": int((closed.status == "withdrawn").sum()), "categories": cats,
            "by_stage": matrix}


def fairness(apps: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Tỷ lệ qua vòng theo giới tính & tỷ lệ tác động bất lợi (quy tắc 4/5)."""
    if apps.empty or events.empty or "gender" not in apps:
        return {"stages": []}
    merged = events.merge(apps[["id", "gender"]], left_on="application_id", right_on="id")
    merged = merged[merged.gender.isin(["Nam", "Nữ"])]
    rows = []
    for code in PIPELINE[1:-1]:
        st = merged[(merged.stage == code) & merged.outcome.isin(["passed", "failed", "no_show"])]
        groups = {}
        for g, grp in st.groupby("gender"):
            groups[g] = {"n": int(len(grp)), "pass_rate_pct": _pct((grp.outcome == "passed").sum(), len(grp))}
        rates = [v["pass_rate_pct"] for v in groups.values() if v["pass_rate_pct"] is not None and v["n"] >= 5]
        air = round(min(rates) / max(rates), 2) if len(rates) == 2 and max(rates) > 0 else None
        min_n = min((v["n"] for v in groups.values()), default=0)
        rows.append({"stage": code, "stage_name": SHORT_NAMES[code], "groups": groups, "impact_ratio": air,
                     "flag": bool(air is not None and air < 0.8 and min_n >= 10),
                     "small_sample": min_n < 10})
    return {"stages": rows, "rule": "Tỷ lệ tác động (impact ratio) < 0,8 (quy tắc 4/5) cần được xem xét; "
                                    "mẫu nhỏ (<10) chỉ mang tính tham khảo."}


def dashboard(db: Session, user: User, filters: Filters | None = None) -> dict:
    apps, events = load_frames(db, user, filters)
    data = {
        "kpis": kpis(apps, events),
        "funnel": funnel(apps, events),
        "stage_durations": stage_durations(events),
        "bottlenecks": bottlenecks(apps, events),
        "sources": source_performance(apps, events),
        "trend": weekly_trend(apps, events),
        "positions": position_pipeline(apps),
        "rejections": rejection_stats(apps),
        "stuck": stuck_applications(apps, events)[:30],
    }
    return data
