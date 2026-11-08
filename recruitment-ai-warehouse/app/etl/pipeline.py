"""Điều phối quy trình ETL đa nguồn và ghi log chi tiết vào bảng etl_run."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.etl.extract import CvLocator, RawItem, detect_source, extract_email, extract_file
from app.etl.load import WarehouseLoader
from app.etl.transform import TransformError, transform_item
from app.models import EtlRun, RawRecord
from app.utils import now_vn

SOURCE_LABELS = {
    "GOOGLE_FORM": "Google Form", "ATS": "ATS", "ATS_JOB": "ATS (vị trí)", "EXCEL": "Excel HR", "EMAIL": "Email",
}
MAX_WARNING_LINES = 40


class RunLogger:
    def __init__(self):
        self.lines: list[str] = []
        self.warning_count = 0

    def __call__(self, level: str, message: str) -> None:
        if level == "WARN":
            self.warning_count += 1
            if self.warning_count > MAX_WARNING_LINES:
                return
        self.lines.append(f"[{now_vn():%Y-%m-%d %H:%M:%S}] {level:<9} {message}")

    def text(self) -> str:
        extra = self.warning_count - MAX_WARNING_LINES
        if extra > 0:
            self.lines.append(f"... và {extra} cảnh báo khác (xem bảng stg_raw_record)")
        return "\n".join(self.lines)


def fingerprint(item: RawItem) -> str:
    raw = json.dumps(item.payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(f"{item.source_system}|{raw}".encode()).hexdigest()


def collect_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.is_file()))
        elif path.is_file():
            files.append(path)
    return files


def run_etl(db: Session, paths: list[Path], triggered_by: int | None = None,
            extra_cv_dirs: list[Path] | None = None) -> EtlRun:
    started = time.perf_counter()
    log = RunLogger()
    files = collect_files(paths)
    data_files = [f for f in files if detect_source(f) not in (None, "CV_FILE")]
    run = EtlRun(triggered_by=triggered_by, sources=[f.name for f in data_files], status="running")
    db.add(run)
    db.commit()
    log("START", f"ETL run #{run.id} – {len(data_files)} tệp dữ liệu, {len(files) - len(data_files)} tệp CV/khác")

    try:
        cv_dirs = sorted({f.parent for f in files}) + (extra_cv_dirs or []) + [get_settings().sample_data_dir / "cvs"]
        cvs = CvLocator(cv_dirs)
        log("INFO", f"Chỉ mục CV: {len(cvs.index)} tệp CV khả dụng (PDF/DOCX/TXT)")

        # ---------------------------------------------------------------- EXTRACT
        items: list[RawItem] = []
        email_no = 0
        for f in data_files:
            try:
                if detect_source(f) == "EMAIL":
                    email_no += 1
                    result = extract_email(f, record_no=email_no)
                else:
                    result = extract_file(f)
            except Exception as exc:  # noqa: BLE001
                log("ERROR", f"Không đọc được {f.name}: {exc}")
                continue
            items.extend(result.items)
            for msg in result.messages:
                log("EXTRACT", msg)
        if email_no:
            log("EXTRACT", f"Hộp thư tuyển dụng: {email_no} email (.eml)")
        per_source: dict[str, int] = {}
        for it in items:
            per_source[it.source_system] = per_source.get(it.source_system, 0) + 1
        log("EXTRACT", "Tổng bản ghi thô: " + ", ".join(f"{SOURCE_LABELS.get(k, k)}={v}" for k, v in per_source.items()))

        # -------------------------------------------------- STAGING + TRANSFORM + LOAD
        loader = WarehouseLoader(db)
        seen = set(db.scalars(select(RawRecord.fingerprint).where(RawRecord.status == "loaded")))
        counts = {"extracted": len(items), "skipped_unchanged": 0, "valid": 0, "rejected": 0}
        reject_reasons: dict[str, int] = {}
        # Vị trí trước, sau đó hồ sơ theo thứ tự ưu tiên nguồn; email rút hồ sơ xử lý sau cùng
        priority = {"ATS_JOB": 0, "ATS": 1, "EXCEL": 2, "GOOGLE_FORM": 3, "EMAIL": 4}
        items.sort(key=lambda it: (priority.get(it.source_system, 9), it.source_file, it.record_no))
        deferred: list[tuple[RawItem, RawRecord, object]] = []

        for item in items:
            fp = fingerprint(item)
            if fp in seen:
                counts["skipped_unchanged"] += 1
                continue
            seen.add(fp)
            raw = RawRecord(etl_run_id=run.id, source_system=item.source_system, source_file=item.source_file,
                            record_no=item.record_no, fingerprint=fp, payload=item.payload, status="loaded")
            db.add(raw)
            try:
                if item.source_system == "ATS_JOB":
                    loader.upsert_job(item.payload)
                    continue
                rec = transform_item(item, cvs)
                for w in rec.warnings:
                    log("WARN", f"{item.source_file} dòng/bản ghi {item.record_no}: {w}")
                if rec.update_only:
                    deferred.append((item, raw, rec))
                    continue
                with db.begin_nested():
                    app = loader.load(rec)
                raw.application_id = app.id
                counts["valid"] += 1
            except TransformError as exc:
                raw.status, raw.error = "rejected", str(exc)
                counts["rejected"] += 1
                reject_reasons[str(exc).split("'")[0].strip()] = reject_reasons.get(str(exc).split("'")[0].strip(), 0) + 1
                log("WARN", f"Loại {item.source_file} bản ghi {item.record_no}: {exc}")

        for item, raw, rec in deferred:
            try:
                with db.begin_nested():
                    app = loader.load(rec)
                raw.application_id = app.id
                counts["valid"] += 1
                log("INFO", f"{item.source_file}: cập nhật hồ sơ {app.application_code} → rút hồ sơ")
            except TransformError as exc:
                raw.status, raw.error = "rejected", str(exc)
                counts["rejected"] += 1
                log("WARN", f"Loại {item.source_file}: {exc}")

        log("TRANSFORM", f"Hợp lệ {counts['valid']} | bị loại {counts['rejected']} | "
                         f"bỏ qua do đã nạp trước đó {counts['skipped_unchanged']}")
        for reason, n in sorted(reject_reasons.items(), key=lambda kv: -kv[1]):
            log("TRANSFORM", f"  · {reason}: {n}")

        loader.finalize()
        s = loader.stats
        if s.get("positions_created") or s.get("positions_updated"):
            log("LOAD", f"dim_position: +{s['positions_created']} mới, {s['positions_updated']} cập nhật (từ ATS)")
        log("LOAD", f"dim_candidate: +{s['candidates_created']} ứng viên mới, gộp {s['duplicates_merged']} bản ghi trùng "
                    f"(email={s['dedup_by_email']}, SĐT={s['dedup_by_phone']}, họ tên+ngày sinh={s['dedup_by_name+dob']})")
        log("LOAD", f"fact_application: +{s['applications_created']} hồ sơ mới, {s['applications_merged']} hồ sơ trùng "
                    f"được gộp, {s['applications_updated']} cập nhật trạng thái")
        log("LOAD", f"fact_stage_event: +{s['events_created']} sự kiện, {s['events_merged']} sự kiện gộp")
        log("NLP", f"Trích xuất kỹ năng cho {s['skills_extracted']} ứng viên; phân loại {s['reasons_classified']} "
                   f"lý do loại/rút hồ sơ")

        db.commit()
        run.status = "success" if counts["rejected"] == 0 else "partial"
        run.stats = {**counts, **dict(s), "warnings": log.warning_count}
        log("DONE", f"Hoàn tất sau {time.perf_counter() - started:.2f}s – trạng thái: {run.status.upper()}")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        run = db.get(EtlRun, run.id)
        run.status = "failed"
        log("ERROR", f"ETL thất bại: {exc!r}")
    run.finished_at = now_vn()
    run.log = log.text()
    db.commit()
    return run
