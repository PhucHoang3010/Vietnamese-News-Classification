"""API nhập dữ liệu (ETL) từ nhiều nguồn và xem nhật ký ETL."""
from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.etl.extract import detect_source
from app.etl.pipeline import run_etl
from app.models import EtlRun, RawRecord, User
from app.rbac import require
from app.serializers import iso
from app.services.audit import log_action
from app.utils import now_vn

router = APIRouter(prefix="/etl", tags=["ETL"])
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def run_out(run: EtlRun, with_log: bool = False) -> dict:
    data = {"id": run.id, "status": run.status, "started_at": iso(run.started_at), "finished_at": iso(run.finished_at),
            "sources": run.sources, "stats": run.stats, "triggered_by": run.triggered_by}
    if with_log:
        data["log"] = run.log
    return data


@router.post("/run")
async def run(files: list[UploadFile] | None = File(None), use_sample: bool = Form(False),
              db: Session = Depends(get_db), user: User = Depends(require("etl:run"))):
    settings = get_settings()
    paths: list[Path] = []
    if files:
        folder = settings.upload_dir / f"upload_{now_vn():%Y%m%d_%H%M%S}_{user.id}"
        folder.mkdir(parents=True, exist_ok=True)
        for f in files:
            name = re.sub(r"[^\w.\-]", "_", Path(f.filename or "file").name)
            if detect_source(Path(name)) is None:
                raise HTTPException(status_code=400, detail=f"Định dạng không hỗ trợ: {f.filename}")
            data = await f.read()
            if len(data) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail=f"{f.filename} vượt quá 20MB")
            (folder / name).write_bytes(data)
        paths.append(folder)
    if use_sample:
        paths.append(settings.sample_data_dir)
    if not paths:
        raise HTTPException(status_code=400, detail="Hãy tải lên ít nhất một tệp hoặc chọn dùng dữ liệu mẫu")
    result = run_etl(db, paths, triggered_by=user.id)
    log_action(db, user, "etl:run", "etl_run", result.id, status=result.status, files=result.sources)
    db.commit()
    return run_out(result, with_log=True)


@router.get("/runs")
def list_runs(db: Session = Depends(get_db), _: User = Depends(require("etl:run"))):
    return [run_out(r) for r in db.scalars(select(EtlRun).order_by(EtlRun.id.desc()).limit(50))]


@router.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db), _: User = Depends(require("etl:run"))):
    run = db.get(EtlRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lần chạy ETL")
    data = run_out(run, with_log=True)
    rejected = db.scalars(select(RawRecord).where(RawRecord.etl_run_id == run_id, RawRecord.status == "rejected"))
    data["rejected_records"] = [{"source_system": r.source_system, "source_file": r.source_file,
                                 "record_no": r.record_no, "error": r.error} for r in rejected]
    data["staging_counts"] = dict(db.execute(
        select(RawRecord.source_system, func.count()).where(RawRecord.etl_run_id == run_id)
        .group_by(RawRecord.source_system)).all())
    return data
