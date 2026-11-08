"""Khởi tạo CSDL: tạo bảng, dữ liệu tham chiếu, tài khoản demo và (tuỳ chọn) nạp dữ liệu mẫu."""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.etl.load import ensure_dates
from app.reference import DEMO_USERS, DEPARTMENTS, POSITIONS, SOURCES, STAGES
from app.security import hash_password

logger = logging.getLogger("talentlens.seed")


def create_schema() -> None:
    Base.metadata.create_all(bind=engine)


def seed_reference(db: Session) -> None:
    depts = {d.code: d for d in db.scalars(select(models.Department))}
    for code, name in DEPARTMENTS:
        if code not in depts:
            depts[code] = models.Department(code=code, name=name)
            db.add(depts[code])
    existing_sources = {s.code for s in db.scalars(select(models.Source))}
    for code, name, channel, _aliases in SOURCES:
        if code not in existing_sources:
            db.add(models.Source(code=code, name=name, channel=channel))
    existing_stages = {s.code for s in db.scalars(select(models.Stage))}
    for code, name, order, sla, terminal, _aliases in STAGES:
        if code not in existing_stages:
            db.add(models.Stage(code=code, name=name, stage_order=order, sla_days=sla, is_terminal=terminal))
    db.flush()
    ensure_dates(db, date(2025, 1, 1), date(2027, 12, 31))

    settings = get_settings()
    users = {u.username: u for u in db.scalars(select(models.User))}
    for spec in DEMO_USERS:
        if spec["username"] in users:
            continue
        password = settings.admin_password if spec["role"] == "admin" else settings.demo_password
        user = models.User(
            username=spec["username"], full_name=spec["full_name"], email=spec["email"], role=spec["role"],
            department_id=depts[spec["department"]].id if spec["department"] else None,
            hashed_password=hash_password(password),
        )
        db.add(user)
        users[spec["username"]] = user
    db.flush()

    positions = {p.code for p in db.scalars(select(models.Position))}
    for spec in POSITIONS:
        if spec["code"] in positions:
            continue
        manager = users.get(spec["manager"]) if spec["manager"] else None
        db.add(models.Position(
            code=spec["code"], title=spec["title"], department_id=depts[spec["department"]].id, level=spec["level"],
            location=spec["location"], headcount=spec["headcount"], jd_text=spec["jd"],
            required_skills=spec["required_skills"], nice_to_have_skills=spec["nice_to_have_skills"],
            aliases=spec["aliases"], hiring_manager_id=manager.id if manager else None, opened_date=spec["opened"],
        ))
    db.commit()


def seed_sample_data(db: Session) -> models.EtlRun | None:
    from app.etl.pipeline import run_etl

    if db.scalar(select(func.count(models.Application.id))):
        return None
    sample_dir = get_settings().sample_data_dir
    if not sample_dir.exists():
        logger.warning("Không tìm thấy thư mục dữ liệu mẫu %s", sample_dir)
        return None
    admin = db.scalar(select(models.User).where(models.User.username == "admin"))
    run = run_etl(db, [sample_dir], triggered_by=admin.id if admin else None)
    logger.info("Đã nạp dữ liệu mẫu: ETL run #%s – %s", run.id, run.status)
    return run


def init_database(load_sample: bool | None = None) -> None:
    create_schema()
    with SessionLocal() as db:
        seed_reference(db)
        if load_sample if load_sample is not None else get_settings().seed_demo:
            seed_sample_data(db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
