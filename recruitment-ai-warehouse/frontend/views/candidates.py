"""Danh sách hồ sơ ứng tuyển + chi tiết ứng viên, hành trình tuyển dụng, nhận xét AI, ghi nhận kết quả vòng."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import api
import ui

st.title("👥 Ứng viên & hồ sơ ứng tuyển")
meta = api.meta()
if not ui.can("pii:read"):
    ui.callout("🛡️ Bạn đang xem ở chế độ <b>ẩn danh</b>: họ tên, email, SĐT, giới tính, ngày sinh, nơi ở của ứng viên "
               "được che để giảm thiên vị khi đánh giá. Nhận xét AI chỉ hiển thị khi HR đã kiểm duyệt.", "info")

c1, c2, c3, c4, c5 = st.columns([1.6, 1.4, 1, 1, 0.8])
with c1:
    q = st.text_input("Tìm kiếm", placeholder="Tên, email, SĐT, mã UV/HS" if ui.can("pii:read") else "Mã UV / mã hồ sơ")
positions = {p["title"]: p["id"] for p in meta["positions"]}
with c2:
    pos_name = st.selectbox("Vị trí", ["Tất cả"] + list(positions))
stages = {s["name"]: s["code"] for s in meta["stages"]}
with c3:
    stage_name = st.selectbox("Vòng hiện tại", ["Tất cả"] + list(stages))
status_opts = {"Tất cả": None, "Đang xử lý": "active", "Đã nhận việc": "hired", "Bị loại": "rejected",
               "Rút hồ sơ": "withdrawn"}
with c4:
    status_name = st.selectbox("Trạng thái", list(status_opts))
with c5:
    st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
    over_sla = st.checkbox("Quá SLA")

params = {"page_size": 500, "over_sla": over_sla}
if q:
    params["q"] = q
if pos_name != "Tất cả":
    params["position_id"] = positions[pos_name]
if stage_name != "Tất cả":
    params["stage"] = stages[stage_name]
if status_opts[status_name]:
    params["status"] = status_opts[status_name]

try:
    result = api.get("/applications", params=params)
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()

items = result["items"]
st.caption(f"{result['total']} hồ sơ phù hợp · chọn một dòng để xem chi tiết")
if not items:
    st.info("Không có hồ sơ phù hợp bộ lọc.")
    st.stop()

rows = pd.DataFrame([{
    "Mã HS": a["application_code"], "Ứng viên": a["candidate"]["display_name"],
    "Liên hệ": a["candidate"]["email"] or a["candidate"]["phone"] or "–", "Vị trí": a["position"]["title"],
    "Nguồn": a["source"], "Ngày nộp": ui.fmt_dt(a["applied_at"]), "Vòng hiện tại": a["current_stage_name"],
    "Trạng thái": a["status_label"], "Ngày ở vòng": a["days_in_current_stage"],
    "Quá SLA": "⚠️" if a["over_sla"] else "", "KN (năm)": a["candidate"]["years_experience"],
} for a in items])
event = st.dataframe(rows, hide_index=True, width="stretch", height=380, on_select="rerun",
                     selection_mode="single-row", key="app_table")
selected = event.selection.rows if event and event.selection else []
if not selected:
    st.stop()
app_id = items[selected[0]]["id"]

try:
    detail = api.get(f"/applications/{app_id}")
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()

cand = detail["candidate"]
st.divider()
h1, h2 = st.columns([3, 2])
with h1:
    st.subheader(f"{cand['display_name']}")
    st.markdown(f"{ui.badge(detail['status'])} :gray-badge[{detail['current_stage_name']}] "
                f":blue-badge[{detail['position']['title']}]  <span class='tl-muted'>{detail['application_code']} · "
                f"{cand['candidate_code']} · nguồn {detail['source']}</span>", unsafe_allow_html=True)
with h2:
    if detail.get("over_sla"):
        ui.callout(f"⏰ Hồ sơ ở vòng hiện tại {detail['days_in_current_stage']} ngày – vượt SLA {detail['sla_days']} ngày.")
    if detail.get("rejection_reason"):
        st.caption(f"Lý do: {detail['rejection_reason']} → nhóm **{detail.get('rejection_category') or '–'}**")

tab_profile, tab_journey, tab_cv, tab_ai, tab_decision = st.tabs(
    ["Hồ sơ", "Hành trình tuyển dụng", "CV", "Nhận xét AI", "Ghi nhận kết quả vòng"])

with tab_profile:
    a, b = st.columns(2)
    with a:
        st.markdown(f"**Email:** {cand['email'] or '–'}  \n**SĐT:** {cand['phone'] or '–'}  \n"
                    f"**Giới tính:** {cand['gender'] or ('(ẩn)' if cand['pii_masked'] else '–')}  \n"
                    f"**Ngày sinh:** {ui.fmt_dt(cand['date_of_birth']) if cand['date_of_birth'] else ('(ẩn)' if cand['pii_masked'] else '–')}  \n"
                    f"**Nơi ở:** {cand['city'] or ('(ẩn)' if cand['pii_masked'] else '–')}")
    with b:
        st.markdown(f"**Chức danh hiện tại:** {cand['current_title'] or '–'}  \n"
                    f"**Kinh nghiệm:** {cand['years_experience'] if cand['years_experience'] is not None else '–'} năm  \n"
                    f"**Học vấn:** {cand['education_level'] or '–'}  \n"
                    f"**Mức lương mong muốn:** {detail['expected_salary'] or '–'} triệu  \n"
                    f"**Nguồn dữ liệu:** {', '.join(detail.get('source_systems', [])) or '(ẩn)'}")
    st.markdown("**Kỹ năng (trích xuất tự động & phân nhóm)**")
    for group, skills in (cand.get("skill_groups") or {}).items():
        st.markdown(f"<b>{group}:</b> {ui.chips(skills)}", unsafe_allow_html=True)
    merged = cand.get("merged_identities")
    if isinstance(merged, list) and merged:
        with st.expander(f"🔗 Đã gộp {len(merged)} bản ghi trùng từ các nguồn khác"):
            st.dataframe(pd.DataFrame(merged), hide_index=True, width="stretch")
    if detail.get("other_applications"):
        st.caption("Hồ sơ khác của ứng viên: " + ", ".join(f"{o['application_code']} ({o['position']})"
                                                           for o in detail["other_applications"]))

with tab_journey:
    ev = pd.DataFrame(detail["events"])
    if not ev.empty:
        ev["entered"] = pd.to_datetime(ev.entered_at)
        ev["exited"] = pd.to_datetime(ev.exited_at).fillna(pd.Timestamp.now())
        colors = {"passed": ui.SERIES[0], "pending": "#86b6ef", "failed": ui.STATUS["critical"],
                  "no_show": ui.STATUS["critical"], "withdrawn": ui.STATUS["serious"]}
        fig = go.Figure()
        for _, r in ev.iterrows():
            fig.add_trace(go.Bar(
                y=[r.stage_name], x=[max((r.exited - r.entered).total_seconds() * 1000, 3.6e6)], base=[r.entered],
                orientation="h", marker=dict(color=colors.get(r.outcome, ui.SERIES[0]), cornerradius=4),
                hovertemplate=f"{r.stage_name}<br>{r.outcome_label}<br>{r.duration_days or '–'} ngày<extra></extra>",
                showlegend=False))
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(type="date", tickformat="%d/%m")
        st.plotly_chart(ui.style_fig(fig, 60 + 42 * len(ev)), width="stretch", config={"displayModeBar": False})
        st.caption("Xanh = đạt · xanh nhạt = đang chờ · đỏ = không đạt/vắng · cam = rút hồ sơ")
        table = ev[["stage_name", "entered_at", "exited_at", "duration_days", "outcome_label", "interviewer", "score",
                    "feedback"]].copy()
        table["entered_at"] = table.entered_at.map(lambda v: ui.fmt_dt(v, True))
        table["exited_at"] = table.exited_at.map(lambda v: ui.fmt_dt(v, True))
        table["duration_days"] = pd.to_numeric(table.duration_days, errors="coerce")
        table["score"] = pd.to_numeric(table.score, errors="coerce")
        table[["interviewer", "feedback"]] = table[["interviewer", "feedback"]].fillna("–")
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            "stage_name": "Vòng", "entered_at": "Vào vòng", "exited_at": "Rời vòng", "duration_days": "Số ngày",
            "outcome_label": "Kết quả", "interviewer": "Người PV", "score": "Điểm (1–5)", "feedback": "Nhận xét"})
        flagged = [e for e in detail["events"] if e["bias_flags"]]
        for e in flagged:
            ui.callout(f"⚠️ Nhận xét vòng <b>{e['stage_name']}</b> bị gắn cờ thiên vị "
                       f"({', '.join(sorted({f['category'] for f in e['bias_flags']}))}): “{e['feedback']}”")

with tab_cv:
    if cand.get("cv_text"):
        st.caption(f"Tệp: {cand.get('cv_file_name') or '–'}" + (" · đã ẩn danh" if cand["pii_masked"] else ""))
        st.text_area("Nội dung CV", cand["cv_text"], height=420, disabled=True, label_visibility="collapsed")
    else:
        st.info("Ứng viên chưa có CV đính kèm trong kho (nguồn Excel/ATS không kèm file).")

with tab_ai:
    if ui.can("ai:run"):
        b1, b2, _ = st.columns([1, 1, 2])
        if b1.button("🤖 Tóm tắt & phân tích CV", width="stretch"):
            with st.spinner("AI đang phân tích CV đã ẩn danh…"):
                try:
                    api.post(f"/ai/applications/{app_id}/analyze-cv")
                    st.toast("Đã tạo nhận xét AI – trạng thái Chờ duyệt")
                    st.rerun()
                except api.ApiError as exc:
                    ui.show_error(exc)
        if b2.button("💬 Gợi ý câu hỏi phỏng vấn", width="stretch"):
            with st.spinner("AI đang soạn câu hỏi theo JD…"):
                try:
                    api.post(f"/ai/applications/{app_id}/interview-questions")
                    st.toast("Đã tạo bộ câu hỏi – trạng thái Chờ duyệt")
                    st.rerun()
                except api.ApiError as exc:
                    ui.show_error(exc)
    insights = detail.get("insights", [])
    if not insights:
        st.info("Chưa có nhận xét AI " + ("nào." if ui.can("ai:read_all") else "đã được HR kiểm duyệt cho hồ sơ này."))
    for ins in insights:
        with st.expander(f"{ins['type_label']} · {ins['status_label']} · {ui.fmt_dt(ins['created_at'], True)}",
                         expanded=ins is insights[0]):
            ui.render_insight(ins)

with tab_decision:
    if not ui.can("feedback:write"):
        st.info("Bạn không có quyền ghi nhận kết quả.")
    elif detail["status"] != "active":
        st.info("Hồ sơ đã đóng.")
    else:
        st.markdown(f"Vòng hiện tại: **{detail['current_stage_name']}**")
        with st.form("decision"):
            decision = st.radio("Kết quả", ["pass", "fail", "withdraw", "no_show"], horizontal=True,
                                format_func={"pass": "Đạt – chuyển vòng tiếp", "fail": "Không đạt",
                                             "withdraw": "Ứng viên rút", "no_show": "Vắng mặt"}.get)
            score = st.slider("Điểm đánh giá (1–5, theo scorecard)", 1.0, 5.0, 3.5, 0.5)
            feedback = st.text_area("Nhận xét (chỉ dựa trên năng lực & yêu cầu công việc)")
            reason = st.text_input("Lý do (nếu không đạt/rút)")
            force = st.checkbox("Vẫn lưu nếu bị gắn cờ thiên vị (sẽ được ghi nhận để kiểm tra)")
            if st.form_submit_button("Lưu kết quả", type="primary"):
                try:
                    api.post(f"/applications/{app_id}/decision", json={
                        "decision": decision, "score": score, "feedback": feedback or None, "reason": reason or None,
                        "force": force})
                    st.success("Đã cập nhật hồ sơ.")
                    st.rerun()
                except api.ApiError as exc:
                    if exc.status == 422 and isinstance(exc.detail, dict):
                        st.warning(exc.detail["message"])
                        for f in exc.detail.get("bias_flags", []):
                            st.markdown(f"- **{f['category']}**: “{f['term']}” – {f['snippet']}")
                    else:
                        ui.show_error(exc)
