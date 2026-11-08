"""Nhập dữ liệu đa nguồn (ETL): tải tệp, chạy ETL, xem log & bản ghi bị loại."""
import io
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

import api
import ui

st.title("📥 Nhập dữ liệu tuyển dụng (ETL)")
st.caption("Hỗ trợ: Google Form (.csv), ATS (.json), Excel HR (.xlsx), email ứng tuyển/rút hồ sơ (.eml), CV (.pdf/.docx/.txt). "
           "Hệ thống chuẩn hoá ứng viên, vị trí, nguồn, vòng, trạng thái; khử trùng theo email → SĐT → họ tên + ngày sinh; "
           "bản ghi đã nạp sẽ được bỏ qua ở lần chạy sau.")

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "raw"
with st.container(border=True):
    files = st.file_uploader("Chọn các tệp dữ liệu", accept_multiple_files=True,
                             type=["csv", "json", "xlsx", "eml", "pdf", "docx", "txt"])
    c1, c2, c3 = st.columns([1.2, 1, 1.4])
    use_sample = c1.checkbox("Kèm bộ dữ liệu mẫu có sẵn trên máy chủ")
    run = c2.button("▶️ Chạy ETL", type="primary", disabled=not (files or use_sample))
    if SAMPLE.exists():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in SAMPLE.rglob("*"):
                if p.is_file():
                    zf.write(p, p.relative_to(SAMPLE))
        c3.download_button("⬇️ Tải bộ dữ liệu mẫu (.zip)", buf.getvalue(), file_name="du_lieu_tuyen_dung_mau.zip")

if run:
    with st.spinner("Đang Extract → Transform → Load…"):
        try:
            payload = [("files", (f.name, f.getvalue())) for f in files] if files else None
            result = api.post("/etl/run", files=payload, data={"use_sample": str(use_sample).lower()})
            st.session_state["etl_result"] = result
        except api.ApiError as exc:
            ui.show_error(exc)

result = st.session_state.get("etl_result")
if result:
    s = result["stats"]
    st.markdown(f"### Kết quả ETL run #{result['id']} – {result['status'].upper()}")
    m = st.columns(6)
    m[0].metric("Bản ghi thô", s.get("extracted", 0))
    m[1].metric("Hợp lệ", s.get("valid", 0))
    m[2].metric("Bị loại", s.get("rejected", 0))
    m[3].metric("Bỏ qua (đã nạp)", s.get("skipped_unchanged", 0))
    m[4].metric("Ứng viên mới", s.get("candidates_created", 0))
    m[5].metric("Bản ghi trùng đã gộp", s.get("duplicates_merged", 0))
    st.code(result["log"], language="log")

st.markdown("### Lịch sử chạy ETL")
try:
    runs = api.get("/etl/runs")
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()
if runs:
    df = pd.DataFrame([{"Run": r["id"], "Trạng thái": r["status"], "Bắt đầu": ui.fmt_dt(r["started_at"], True),
                        "Tệp": len(r["sources"]), "Bản ghi": r["stats"].get("extracted"),
                        "Hợp lệ": r["stats"].get("valid"), "Bị loại": r["stats"].get("rejected"),
                        "Bỏ qua": r["stats"].get("skipped_unchanged"),
                        "Ứng viên mới": r["stats"].get("candidates_created"),
                        "Gộp trùng": r["stats"].get("duplicates_merged")} for r in runs])
    st.dataframe(df, hide_index=True, width="stretch")
    pick = st.selectbox("Xem chi tiết run", [r["id"] for r in runs], format_func=lambda i: f"Run #{i}")
    detail = api.get(f"/etl/runs/{pick}")
    t1, t2 = st.tabs(["Log", "Bản ghi bị loại"])
    with t1:
        st.code(detail["log"], language="log")
        if detail.get("staging_counts"):
            st.caption("Bản ghi lưu ở vùng staging (stg_raw_record): " +
                       ", ".join(f"{k}: {v}" for k, v in detail["staging_counts"].items()))
    with t2:
        if detail["rejected_records"]:
            st.dataframe(pd.DataFrame(detail["rejected_records"]).rename(columns={
                "source_system": "Nguồn", "source_file": "Tệp", "record_no": "Dòng/Bản ghi", "error": "Lý do"}),
                hide_index=True, width="stretch")
        else:
            st.success("Không có bản ghi bị loại.")
