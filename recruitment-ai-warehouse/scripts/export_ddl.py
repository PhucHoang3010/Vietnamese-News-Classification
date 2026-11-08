"""Xuất DDL PostgreSQL của kho dữ liệu từ mô hình SQLAlchemy → sql/schema.sql"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.schema import CreateIndex, CreateTable  # noqa: E402

from app.database import Base  # noqa: E402
import app.models  # noqa: E402,F401

ORDER = ["dim_department", "app_user", "dim_source", "dim_stage", "dim_date", "dim_position", "dim_candidate",
         "fact_application", "fact_stage_event", "etl_run", "stg_raw_record", "ai_insight", "weekly_report",
         "audit_log"]

lines = ["-- DDL kho dữ liệu tuyển dụng TalentLens (PostgreSQL 16)",
         "-- Sinh tự động từ app/models.py bằng scripts/export_ddl.py", ""]
tables = {t.name: t for t in Base.metadata.sorted_tables}
for name in ORDER:
    table = tables[name]
    lines.append(str(CreateTable(table).compile(dialect=postgresql.dialect())).strip() + ";")
    for index in table.indexes:
        lines.append(str(CreateIndex(index).compile(dialect=postgresql.dialect())).strip() + ";")
    lines.append("")
(ROOT / "sql" / "schema.sql").write_text("\n".join(lines), encoding="utf-8")
print("Đã ghi sql/schema.sql")
