"""Kiểm thử ETL đa nguồn: khử trùng, idempotent, lineage."""
from sqlalchemy import func, select

from app.config import get_settings
from app.etl.pipeline import run_etl
from app.models import Application, Candidate, EtlRun, RawRecord, StageEvent


def test_sample_load_deduplicates(client, db):
    run = db.scalar(select(EtlRun).order_by(EtlRun.id))
    assert run.status in ("success", "partial")
    # Bộ dữ liệu mẫu có 314 người thật / 329 hồ sơ thật, rải trên 4 nguồn với nhiều bản ghi trùng
    assert db.scalar(select(func.count(Candidate.id))) == 314
    assert db.scalar(select(func.count(Application.id))) == 329
    assert run.stats["duplicates_merged"] > 100
    assert run.stats["rejected"] == 5  # các bản ghi lỗi được cài sẵn
    errors = set(db.scalars(select(RawRecord.error).where(RawRecord.status == "rejected")))
    assert any("không xác định được vị trí" in e for e in errors)
    assert any("thiếu thông tin liên hệ" in e for e in errors)


def test_no_duplicate_emails_or_negative_durations(client, db):
    dup = db.execute(select(Candidate.email, func.count()).where(Candidate.email.is_not(None))
                     .group_by(Candidate.email).having(func.count() > 1)).all()
    assert dup == []
    assert db.scalar(select(func.count(StageEvent.id)).where(StageEvent.duration_hours < 0)) == 0


def test_withdrawal_emails_update_status(client, db):
    run = db.scalar(select(EtlRun).order_by(EtlRun.id))
    assert "rút hồ sơ" in run.log
    withdrawn = db.scalar(select(func.count(Application.id)).where(Application.status == "withdrawn"))
    assert withdrawn == 48


def test_rerun_is_idempotent(client, db):
    before = db.scalar(select(func.count(Application.id)))
    run = run_etl(db, [get_settings().sample_data_dir])
    assert run.stats["valid"] == 0 and run.stats["skipped_unchanged"] > 400
    assert db.scalar(select(func.count(Application.id))) == before
