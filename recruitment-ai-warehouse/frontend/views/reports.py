"""Báo cáo pipeline tuần: tạo (AI hỗ trợ), duyệt, tải về."""
from datetime import date, timedelta

import streamlit as st

import api
import ui

st.title("📝 Báo cáo pipeline tuần")
if ui.can("reports:generate"):
    with st.container(border=True):
        c1, c2 = st.columns([1, 2])
        today = date.today()
        default = today - timedelta(days=today.weekday() + 7)
        week = c1.date_input("Tuần bắt đầu (thứ Hai)", value=default, format="DD/MM/YYYY")
        c2.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
        if c2.button("Tạo báo cáo tuần", type="primary"):
            with st.spinner("Đang tổng hợp số liệu và viết nhận định…"):
                try:
                    rep = api.post("/reports/weekly", json={"week_start": week.isoformat()})
                    st.session_state["report_id"] = rep["id"]
                    st.toast("Đã tạo bản nháp báo cáo")
                except api.ApiError as exc:
                    ui.show_error(exc)
else:
    st.caption("Bạn đang xem các báo cáo đã được HR duyệt.")

try:
    reports = api.get("/reports")
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()
if not reports:
    st.info("Chưa có báo cáo.")
    st.stop()

labels = {f"Tuần {ui.fmt_dt(r['week_start'])} – {ui.fmt_dt(r['week_end'])} · {r['status_label']} · #{r['id']}": r["id"]
          for r in reports}
ids = list(labels.values())
default_index = ids.index(st.session_state["report_id"]) if st.session_state.get("report_id") in ids else 0
choice = st.selectbox("Chọn báo cáo", list(labels), index=default_index)
rep = api.get(f"/reports/{labels[choice]}")

c1, c2, c3, c4 = st.columns([1.2, 1, 1, 2])
c1.markdown(f"{ui.badge(rep['status'])} <span class='tl-muted'>AI: {rep['provider']}</span>", unsafe_allow_html=True)
md = api.get(f"/reports/{rep['id']}/download", params={"format": "md"}, raw=True).text
html = api.get(f"/reports/{rep['id']}/download", params={"format": "html"}, raw=True).text
c2.download_button("⬇️ Markdown", md, file_name=f"bao_cao_tuan_{rep['week_start']}.md", mime="text/markdown")
c3.download_button("⬇️ HTML", html, file_name=f"bao_cao_tuan_{rep['week_start']}.html", mime="text/html")
if rep["status"] != "approved" and ui.can("reports:approve"):
    if c4.button("✅ Duyệt & phát hành cho quản lý", type="primary"):
        try:
            api.post(f"/reports/{rep['id']}/approve")
            st.rerun()
        except api.ApiError as exc:
            ui.show_error(exc)
if rep["bias_flags"]:
    ui.callout("⚠️ Phần nhận định có nội dung bị gắn cờ thiên vị – vui lòng rà soát trước khi duyệt.")
with st.container(border=True):
    st.markdown(rep["narrative"])
