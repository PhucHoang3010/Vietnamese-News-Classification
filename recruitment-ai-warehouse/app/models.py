"""Mô hình kho dữ liệu tuyển dụng (lược đồ hình sao) + các bảng vận hành.

Tầng dữ liệu:
  * stg_*  : vùng staging lưu bản ghi thô từ từng nguồn (phục vụ truy vết - lineage)
  * dim_*  : bảng chiều (ứng viên, vị trí, nguồn, vòng tuyển dụng, phòng ban, ngày)
  * fact_* : bảng sự kiện (hồ sơ ứng tuyển, sự kiện qua từng vòng)
  * app_*, ai_*, etl_*, audit_* : bảng vận hành của ứng dụng web
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import now_vn

JSONType = JSON().with_variant(JSONB(), "postgresql")


# --------------------------------------------------------------------------- #
# Bảng chiều (Dimensions)
# --------------------------------------------------------------------------- #
class Department(Base):
    __tablename__ = "dim_department"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))

    positions: Mapped[list[Position]] = relationship(back_populates="department")


class Source(Base):
    __tablename__ = "dim_source"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    channel: Mapped[str] = mapped_column(String(40))  # job_board, referral, social...


class Stage(Base):
    __tablename__ = "dim_stage"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    stage_order: Mapped[int] = mapped_column(Integer)
    sla_days: Mapped[int] = mapped_column(Integer, default=5)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False)


class DateDim(Base):
    __tablename__ = "dim_date"

    date_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)  # YYYYMMDD
    full_date: Mapped[date] = mapped_column(Date, unique=True)
    day: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    quarter: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    iso_week: Mapped[int] = mapped_column(Integer)
    week_start: Mapped[date] = mapped_column(Date)
    day_of_week: Mapped[int] = mapped_column(Integer)  # 1 = Thứ Hai
    is_weekend: Mapped[bool] = mapped_column(Boolean)


class Position(Base):
    __tablename__ = "dim_position"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    department_id: Mapped[int] = mapped_column(ForeignKey("dim_department.id"))
    level: Mapped[str | None] = mapped_column(String(40))
    location: Mapped[str | None] = mapped_column(String(80))
    headcount: Mapped[int] = mapped_column(Integer, default=1)
    jd_text: Mapped[str | None] = mapped_column(Text)
    required_skills: Mapped[list] = mapped_column(JSONType, default=list)
    nice_to_have_skills: Mapped[list] = mapped_column(JSONType, default=list)
    aliases: Mapped[list] = mapped_column(JSONType, default=list)
    hiring_manager_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    status: Mapped[str] = mapped_column(String(20), default="open")
    opened_date: Mapped[date | None] = mapped_column(Date)

    department: Mapped[Department] = relationship(back_populates="positions")
    hiring_manager: Mapped[User | None] = relationship(foreign_keys=[hiring_manager_id])


class Candidate(Base):
    __tablename__ = "dim_candidate"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_code: Mapped[str] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(160), index=True)
    phone: Mapped[str | None] = mapped_column(String(20), index=True)
    # Thuộc tính nhạy cảm: chỉ HR/Admin xem, KHÔNG BAO GIỜ gửi cho AI
    gender: Mapped[str | None] = mapped_column(String(10))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    city: Mapped[str | None] = mapped_column(String(80))
    # Thuộc tính nghề nghiệp
    years_experience: Mapped[float | None] = mapped_column(Float)
    education_level: Mapped[str | None] = mapped_column(String(40))
    current_title: Mapped[str | None] = mapped_column(String(160))
    skills: Mapped[list] = mapped_column(JSONType, default=list)
    skill_groups: Mapped[dict] = mapped_column(JSONType, default=dict)
    cv_text: Mapped[str | None] = mapped_column(Text)
    cv_file_name: Mapped[str | None] = mapped_column(String(255))
    first_source_id: Mapped[int | None] = mapped_column(ForeignKey("dim_source.id"))
    merged_identities: Mapped[list] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn, onupdate=now_vn)

    applications: Mapped[list[Application]] = relationship(back_populates="candidate")


# --------------------------------------------------------------------------- #
# Bảng sự kiện (Facts)
# --------------------------------------------------------------------------- #
class Application(Base):
    __tablename__ = "fact_application"
    __table_args__ = (UniqueConstraint("candidate_id", "position_id", name="uq_application_candidate_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    application_code: Mapped[str] = mapped_column(String(20), unique=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("dim_candidate.id"), index=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("dim_position.id"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("dim_source.id"), index=True)
    applied_date_key: Mapped[int] = mapped_column(ForeignKey("dim_date.date_key"), index=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime)
    current_stage_id: Mapped[int] = mapped_column(ForeignKey("dim_stage.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|hired|rejected|withdrawn|on_hold
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    rejection_category: Mapped[str | None] = mapped_column(String(40))
    expected_salary: Mapped[float | None] = mapped_column(Float)  # triệu VND/tháng
    source_systems: Mapped[list] = mapped_column(JSONType, default=list)
    external_ids: Mapped[list] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn, onupdate=now_vn)

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    position: Mapped[Position] = relationship()
    source: Mapped[Source] = relationship()
    current_stage: Mapped[Stage] = relationship()
    events: Mapped[list[StageEvent]] = relationship(
        back_populates="application", order_by="StageEvent.entered_at", cascade="all, delete-orphan"
    )


class StageEvent(Base):
    __tablename__ = "fact_stage_event"
    __table_args__ = (UniqueConstraint("application_id", "stage_id", name="uq_event_application_stage"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("fact_application.id", ondelete="CASCADE"), index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("dim_stage.id"), index=True)
    entered_at: Mapped[datetime] = mapped_column(DateTime)
    exited_at: Mapped[datetime | None] = mapped_column(DateTime)
    outcome: Mapped[str] = mapped_column(String(20), default="pending")  # passed|failed|withdrawn|pending|no_show
    duration_hours: Mapped[float | None] = mapped_column(Float)
    interviewer: Mapped[str | None] = mapped_column(String(120))
    score: Mapped[float | None] = mapped_column(Float)
    feedback: Mapped[str | None] = mapped_column(Text)
    bias_flags: Mapped[list] = mapped_column(JSONType, default=list)
    source_system: Mapped[str | None] = mapped_column(String(30))

    application: Mapped[Application] = relationship(back_populates="events")
    stage: Mapped[Stage] = relationship()


# --------------------------------------------------------------------------- #
# Staging & vận hành
# --------------------------------------------------------------------------- #
class EtlRun(Base):
    __tablename__ = "etl_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running|success|partial|failed
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    sources: Mapped[list] = mapped_column(JSONType, default=list)
    stats: Mapped[dict] = mapped_column(JSONType, default=dict)
    log: Mapped[str] = mapped_column(Text, default="")


class RawRecord(Base):
    __tablename__ = "stg_raw_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    etl_run_id: Mapped[int] = mapped_column(ForeignKey("etl_run.id", ondelete="CASCADE"), index=True)
    source_system: Mapped[str] = mapped_column(String(30))
    source_file: Mapped[str] = mapped_column(String(255))
    record_no: Mapped[int] = mapped_column(Integer)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSONType)
    status: Mapped[str] = mapped_column(String(20), default="loaded")  # loaded|rejected
    error: Mapped[str | None] = mapped_column(Text)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("fact_application.id", ondelete="SET NULL"))
    loaded_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn)


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(160))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # admin|hr|hiring_manager
    department_id: Mapped[int | None] = mapped_column(ForeignKey("dim_department.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    department: Mapped[Department | None] = relationship(foreign_keys=[department_id])


class AIInsight(Base):
    __tablename__ = "ai_insight"

    id: Mapped[int] = mapped_column(primary_key=True)
    insight_type: Mapped[str] = mapped_column(String(40))  # cv_analysis|interview_questions|rejection_insights
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("dim_candidate.id", ondelete="CASCADE"))
    application_id: Mapped[int | None] = mapped_column(ForeignKey("fact_application.id", ondelete="CASCADE"))
    position_id: Mapped[int | None] = mapped_column(ForeignKey("dim_position.id"))
    content: Mapped[dict] = mapped_column(JSONType)
    provider: Mapped[str] = mapped_column(String(20))  # claude|local
    model_name: Mapped[str] = mapped_column(String(60))
    prompt_version: Mapped[str] = mapped_column(String(20), default="v1")
    status: Mapped[str] = mapped_column(String(20), default="pending_review")  # pending_review|approved|rejected
    bias_flags: Mapped[list] = mapped_column(JSONType, default=list)
    removed_fields: Mapped[list] = mapped_column(JSONType, default=list)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    review_note: Mapped[str | None] = mapped_column(Text)
    edited: Mapped[bool] = mapped_column(Boolean, default=False)

    candidate: Mapped[Candidate | None] = relationship()
    application: Mapped[Application | None] = relationship()
    position: Mapped[Position | None] = relationship()
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])


class WeeklyReport(Base):
    __tablename__ = "weekly_report"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    week_end: Mapped[date] = mapped_column(Date)
    metrics: Mapped[dict] = mapped_column(JSONType)
    narrative: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|approved
    bias_flags: Mapped[list] = mapped_column(JSONType, default=list)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)

    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])
    approver: Mapped[User | None] = relationship(foreign_keys=[approved_by])


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str | None] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(40))
    detail: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_vn, index=True)

    user: Mapped[User | None] = relationship()
