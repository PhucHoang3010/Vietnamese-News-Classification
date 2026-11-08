"""Nhật ký hệ thống (audit log)."""
import pandas as pd
import streamlit as st

import api
import ui

st.title("🧾 Nhật ký hệ thống")
st.caption("Ghi lại đăng nhập, xem thông tin cá nhân ứng viên, chạy ETL, chạy AI, kiểm duyệt, tạo/duyệt báo cáo, quản lý tài khoản.")
try:
    logs = api.get("/audit-logs", params={"limit": 500})
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()
df = pd.DataFrame([{"Thời gian": ui.fmt_dt(r["created_at"], True), "Người dùng": r["user"] or "–", "Hành động": r["action"],
                    "Đối tượng": f"{r['entity_type'] or ''} {r['entity_id'] or ''}".strip(),
                    "Chi tiết": ", ".join(f"{k}={v}" for k, v in (r["detail"] or {}).items())} for r in logs])
actions = sorted(df["Hành động"].unique()) if not df.empty else []
chosen = st.multiselect("Lọc theo hành động", actions)
if chosen:
    df = df[df["Hành động"].isin(chosen)]
st.dataframe(df, hide_index=True, width="stretch", height=560)
