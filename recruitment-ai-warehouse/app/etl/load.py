"""LOAD – nạp dữ liệu chuẩn vào kho: định danh & khử trùng ứng viên, gộp hồ sơ, sự kiện vòng."""
from __future__ import annotations

import difflib
from collections import Counter, defaultdict
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.bias_guard import scan_text
from app.ai.rejection import classify_reason
from app.ai.skills import extract_skills, group_skills
from app.etl.transform import STAGE_ORDER, CanonicalApplication, TransformError, name_dob_key
from app.models import Application, Candidate, DateDim, Department, Position, Source, Stage, StageEvent
from app.utils import normalize_key, strip_accents


def date_key(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def ensure_dates(db: Session, start: date, end: date) -> int:
    """Bổ sung dim_date cho khoảng ngày [start, end]."""
    existing = set(db.scalars(select(DateDim.date_key).where(DateDim.full_date.between(start, end))))
    added = 0
    d = start
    while d <= end:
        key = date_key(d)
        if key not in existing:
            iso = d.isocalendar()
            db.add(DateDim(
                date_key=key, full_date=d, day=d.day, month=d.month, quarter=(d.month - 1) // 3 + 1, year=d.year,
                iso_week=iso.week, week_start=d - timedelta(days=d.weekday()), day_of_week=d.isoweekday(),
                is_weekend=d.isoweekday() >= 6,
            ))
            added += 1
        d += timedelta(days=1)
    return added


class PositionResolver:
    def __init__(self, db: Session):
        self.db = db
        self.refresh()

    def refresh(self) -> None:
        self.lookup: dict[str, Position] = {}
        for pos in self.db.scalars(select(Position)):
            for key in [pos.code, pos.title, *(pos.aliases or [])]:
                self.lookup[normalize_key(key)] = pos

    def resolve(self, text: str | None) -> Position | None:
        key = normalize_key(text)
        if not key:
            return None
        if key in self.lookup:
            return self.lookup[key]
        padded = f" {key} "
        for alias in sorted(self.lookup, key=len, reverse=True):
            if len(alias) > 3 and f" {alias} " in padded:
                return self.lookup[alias]
        close = difflib.get_close_matches(key, list(self.lookup), n=1, cutoff=0.78)
        return self.lookup[close[0]] if close else None


class IdentityIndex:
    """Chỉ mục định danh ứng viên: email → SĐT → (họ tên + ngày sinh)."""

    def __init__(self, db: Session):
        self.by_email: dict[str, Candidate] = {}
        self.by_phone: dict[str, Candidate] = {}
        self.by_name_dob: dict[str, Candidate] = {}
        for cand in db.scalars(select(Candidate)):
            self.add(cand)

    def add(self, cand: Candidate) -> None:
        if cand.email:
            self.by_email.setdefault(cand.email, cand)
        if cand.phone:
            self.by_phone.setdefault(cand.phone, cand)
        key = name_dob_key(cand.full_name, cand.date_of_birth)
        if key:
            self.by_name_dob.setdefault(key, cand)

    def find(self, rec: CanonicalApplication) -> tuple[Candidate | None, str | None]:
        if rec.email and rec.email in self.by_email:
            return self.by_email[rec.email], "email"
        if rec.phone and rec.phone in self.by_phone:
            return self.by_phone[rec.phone], "phone"
        key = name_dob_key(rec.full_name, rec.date_of_birth)
        if key and key in self.by_name_dob:
            return self.by_name_dob[key], "name+dob"
        return None, None


def _has_accents(text: str) -> bool:
    return strip_accents(text) != text


class WarehouseLoader:
    def __init__(self, db: Session):
        self.db = db
        self.stats: Counter[str] = Counter()
        self.positions = PositionResolver(db)
        self.sources = {s.code: s for s in db.scalars(select(Source))}
        self.stages = {s.code: s for s in db.scalars(select(Stage))}
        self.stage_by_id = {s.id: s for s in self.stages.values()}
        self.departments = {d.code: d for d in db.scalars(select(Department))}
        self.identity = IdentityIndex(db)
        self.apps: dict[tuple[int, int], Application] = {
            (a.candidate_id, a.position_id): a for a in db.scalars(select(Application))
        }
        self.cand_seq = (db.scalar(select(func.count(Candidate.id))) or 0)
        self.app_seq = (db.scalar(select(func.count(Application.id))) or 0)
        self.touched_apps: set[int] = set()
        self.touched_cands: set[int] = set()
        self.extra_skill_text: dict[int, list[str]] = defaultdict(list)
        self.min_date: date | None = None
        self.max_date: date | None = None
        self.known_dates: set[int] = set(db.scalars(select(DateDim.date_key)))

    def _ensure_date(self, d: date) -> int:
        key = date_key(d)
        if key not in self.known_dates:
            ensure_dates(self.db, d, d)
            self.db.flush()
            self.known_dates.add(key)
        return key

    # ------------------------------------------------------------- vị trí
    def upsert_job(self, job: dict) -> Position:
        code = (job.get("req_id") or "").strip()
        if not code:
            raise TransformError("vị trí ATS thiếu mã req_id")
        pos = self.db.scalar(select(Position).where(Position.code == code))
        dept = self.departments.get((job.get("department") or "").upper())
        if pos is None:
            if dept is None:
                raise TransformError(f"phòng ban '{job.get('department')}' không tồn tại")
            pos = Position(code=code, title=job.get("title") or code, department_id=dept.id, aliases=[])
            self.db.add(pos)
            self.stats["positions_created"] += 1
        else:
            self.stats["positions_updated"] += 1
        if job.get("title") and normalize_key(job["title"]) not in [normalize_key(a) for a in pos.aliases or []]:
            pos.aliases = list(pos.aliases or []) + [job["title"]]
        pos.jd_text = job.get("description") or pos.jd_text
        pos.required_skills = job.get("required_skills") or pos.required_skills or []
        pos.nice_to_have_skills = job.get("nice_to_have") or pos.nice_to_have_skills or []
        pos.headcount = job.get("headcount") or pos.headcount
        pos.status = (job.get("status") or pos.status or "open").lower()
        pos.location = job.get("location") or pos.location
        self.db.flush()
        self.positions.refresh()
        return pos

    # ----------------------------------------------------------- ứng viên
    def _resolve_candidate(self, rec: CanonicalApplication, source: Source) -> Candidate:
        cand, matched_by = self.identity.find(rec)
        if cand is None:
            self.cand_seq += 1
            cand = Candidate(
                candidate_code=f"UV-{self.cand_seq:05d}", full_name=rec.full_name, email=rec.email, phone=rec.phone,
                gender=rec.gender, date_of_birth=rec.date_of_birth, city=rec.city,
                years_experience=rec.years_experience, education_level=rec.education_level,
                current_title=rec.current_title, cv_text=rec.cv_text, cv_file_name=rec.cv_file_name,
                first_source_id=source.id, skills=[], skill_groups={}, merged_identities=[],
            )
            self.db.add(cand)
            self.db.flush()
            self.stats["candidates_created"] += 1
        else:
            self.stats["duplicates_merged"] += 1
            self.stats[f"dedup_by_{matched_by}"] += 1
            identity = {"source": rec.source_system, "file": rec.source_file, "row": rec.record_no,
                        "matched_by": matched_by}
            if rec.email and cand.email and rec.email != cand.email:
                identity["other_email"] = rec.email
            if rec.phone and cand.phone and rec.phone != cand.phone:
                identity["other_phone"] = rec.phone
            cand.merged_identities = list(cand.merged_identities or []) + [identity]
            if rec.full_name and (not cand.full_name or (_has_accents(rec.full_name) and not _has_accents(cand.full_name))):
                cand.full_name = rec.full_name
            for attr in ["email", "phone", "gender", "date_of_birth", "city", "years_experience", "education_level",
                         "current_title", "cv_file_name"]:
                if getattr(cand, attr) in (None, "") and getattr(rec, attr) not in (None, ""):
                    setattr(cand, attr, getattr(rec, attr))
            if rec.cv_text and len(rec.cv_text) > len(cand.cv_text or ""):
                cand.cv_text = rec.cv_text
                cand.cv_file_name = rec.cv_file_name or cand.cv_file_name
        self.identity.add(cand)
        if rec.skills_text:
            self.extra_skill_text[cand.id].append(rec.skills_text)
        self.touched_cands.add(cand.id)
        return cand

    # ------------------------------------------------------------- hồ sơ
    def load(self, rec: CanonicalApplication) -> Application:
        position = self.positions.resolve(rec.position_text)
        if position is None:
            raise TransformError(f"không xác định được vị trí '{rec.position_text}'")
        source = self.sources.get(rec.source_code) or self.sources["OTHER"]

        if rec.update_only:
            cand, _ = self.identity.find(rec)
            app = self.apps.get((cand.id, position.id)) if cand else None
            if app is None:
                raise TransformError("email rút hồ sơ không khớp hồ sơ ứng tuyển nào trong kho")
            self._merge_status(app, rec)
            self.touched_apps.add(app.id)
            self.stats["applications_updated"] += 1
            return app

        cand = self._resolve_candidate(rec, source)
        app = self.apps.get((cand.id, position.id))
        applied = rec.applied_at
        if app is None:
            self.app_seq += 1
            app = Application(
                application_code=f"HS-{self.app_seq:05d}", candidate_id=cand.id, position_id=position.id,
                source_id=source.id, applied_at=applied, applied_date_key=self._ensure_date(applied.date()),
                current_stage_id=self.stages["APPLIED"].id, status=rec.status or "active", closed_at=rec.closed_at,
                rejection_reason=rec.rejection_reason, expected_salary=rec.expected_salary,
                source_systems=[rec.source_system], external_ids=[rec.external_id] if rec.external_id else [],
            )
            self.db.add(app)
            self.db.flush()
            self.apps[(cand.id, position.id)] = app
            self.stats["applications_created"] += 1
        else:
            self.stats["applications_merged"] += 1
            if applied < app.applied_at:
                app.applied_at = applied
                app.applied_date_key = self._ensure_date(applied.date())
                app.source_id = source.id  # ghi nhận nguồn chạm đầu tiên (first-touch)
            if rec.source_system not in (app.source_systems or []):
                app.source_systems = list(app.source_systems or []) + [rec.source_system]
            if rec.external_id and rec.external_id not in (app.external_ids or []):
                app.external_ids = list(app.external_ids or []) + [rec.external_id]
            if app.expected_salary is None:
                app.expected_salary = rec.expected_salary
            self._merge_status(app, rec)
        self._track_date(applied.date())
        self._merge_events(app, rec)
        self.touched_apps.add(app.id)
        return app

    def _track_date(self, d: date) -> None:
        self.min_date = d if self.min_date is None else min(self.min_date, d)
        self.max_date = d if self.max_date is None else max(self.max_date, d)

    @staticmethod
    def _merge_status(app: Application, rec: CanonicalApplication) -> None:
        if rec.status in (None, "active"):
            return
        newer = rec.closed_at and (app.closed_at is None or rec.closed_at >= app.closed_at)
        if app.status in ("active", "on_hold") or newer:
            app.status = rec.status
            app.closed_at = rec.closed_at or app.closed_at
            if rec.rejection_reason:
                app.rejection_reason = rec.rejection_reason
        elif rec.rejection_reason and not app.rejection_reason:
            app.rejection_reason = rec.rejection_reason

    def _merge_events(self, app: Application, rec: CanonicalApplication) -> None:
        existing = {ev.stage_id: ev for ev in app.events}
        for cev in rec.events:
            stage = self.stages[cev.stage_code]
            ev = existing.get(stage.id)
            if ev is None:
                ev = StageEvent(application_id=app.id, stage_id=stage.id, entered_at=cev.entered_at,
                                exited_at=cev.exited_at, outcome=cev.outcome or "pending", interviewer=cev.interviewer,
                                score=cev.score, feedback=cev.feedback, source_system=rec.source_system, bias_flags=[])
                app.events.append(ev)
                existing[stage.id] = ev
                self.stats["events_created"] += 1
            else:
                self.stats["events_merged"] += 1
                if cev.entered_at < ev.entered_at:
                    ev.entered_at = cev.entered_at
                if cev.exited_at and (ev.exited_at is None or cev.exited_at > ev.exited_at):
                    ev.exited_at = cev.exited_at
                if cev.outcome and cev.outcome != "pending" and ev.outcome in (None, "pending", "passed"):
                    ev.outcome = cev.outcome
                for attr in ["interviewer", "score", "feedback"]:
                    if getattr(ev, attr) in (None, "") and getattr(cev, attr) not in (None, ""):
                        setattr(ev, attr, getattr(cev, attr))
            self._track_date(cev.entered_at.date())

    # ----------------------------------------------------- tính toán lại
    def finalize(self) -> None:
        """Tính lại vòng hiện tại, thời lượng từng vòng, nhóm lý do rớt, kỹ năng ứng viên."""
        self.db.flush()
        for app in self.db.scalars(select(Application).where(Application.id.in_(self.touched_apps))):
            events = sorted(app.events, key=lambda e: self.stage_by_id[e.stage_id].stage_order)
            if app.status == "hired" and not any(self.stage_by_id[e.stage_id].code == "HIRED" for e in events):
                hired_at = app.closed_at or (events[-1].exited_at if events else app.applied_at) or app.applied_at
                ev = StageEvent(application_id=app.id, stage_id=self.stages["HIRED"].id, entered_at=hired_at,
                                outcome="passed", source_system="DERIVED", bias_flags=[])
                app.events.append(ev)
                events.append(ev)
            for i, ev in enumerate(events):
                last = i == len(events) - 1
                if not last:
                    if ev.exited_at is None:
                        ev.exited_at = events[i + 1].entered_at
                    if ev.outcome in (None, "pending"):
                        ev.outcome = "passed"
                else:
                    code = self.stage_by_id[ev.stage_id].code
                    if code == "HIRED":
                        ev.outcome = "passed"
                        app.status = "hired"
                        app.closed_at = app.closed_at or ev.entered_at
                    elif app.status == "withdrawn":
                        ev.outcome = "withdrawn"
                    elif app.status == "rejected" and ev.outcome not in ("failed", "no_show"):
                        ev.outcome = "failed"
                    if ev.exited_at is None and app.status in ("rejected", "withdrawn") and app.closed_at:
                        ev.exited_at = max(app.closed_at, ev.entered_at)
                if self.stage_by_id[ev.stage_id].code == "HIRED":
                    ev.exited_at = None  # vòng kết thúc, không tính thời lượng
                elif ev.exited_at and ev.exited_at < ev.entered_at:
                    ev.exited_at = ev.entered_at  # dữ liệu nguồn chỉ có ngày (không có giờ)
                ev.duration_hours = (round((ev.exited_at - ev.entered_at).total_seconds() / 3600, 1)
                                     if ev.exited_at else None)
                ev.bias_flags = scan_text(ev.feedback)
            if events:
                app.current_stage_id = events[-1].stage_id
            app.rejection_category = (classify_reason(app.rejection_reason)
                                      if app.status in ("rejected", "withdrawn") else None)
            if app.rejection_category:
                self.stats["reasons_classified"] += 1

        for cand in self.db.scalars(select(Candidate).where(Candidate.id.in_(self.touched_cands))):
            text = (cand.cv_text or "") + "\n" + "\n".join(self.extra_skill_text.get(cand.id, []))
            skills = list(dict.fromkeys(extract_skills(text) + list(cand.skills or [])))
            cand.skills = skills
            cand.skill_groups = group_skills(skills)
            first = min(cand.applications, key=lambda a: a.applied_at, default=None)
            if first:
                cand.first_source_id = first.source_id
            self.stats["skills_extracted"] += 1 if skills else 0
        if self.min_date and self.max_date:
            ensure_dates(self.db, self.min_date, self.max_date)
        self.db.flush()
