"""AI phân tích CV: xử lý CV mẫu/tải lên, gợi ý câu hỏi phỏng vấn, lý do rớt phổ biến."""
from pathlib import Path

import streamlit as st

import api
import ui

st.title("🤖 AI phân tích CV & pipeline")
meta = api.meta()
ai = meta.get("ai", {})
st.caption(("Đang dùng **Claude** (" + ai.get("model", "") + ")") if ai.get("provider") == "claude" else
           "Đang dùng **engine NLP nội bộ** (từ điển kỹ năng + TF-IDF + luật). Cấu hình `ANTHROPIC_API_KEY` để dùng Claude.")
ui.callout("🛡️ Trước khi gửi cho AI, hệ thống tự ẩn họ tên, email, SĐT, ngày sinh, giới tính, hôn nhân, địa chỉ. "
           "AI <b>không chấm điểm hay quyết định tuyển</b>; mọi kết quả lưu ở trạng thái <b>Chờ duyệt</b> để HR kiểm duyệt.",
           "info")

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "cvs"
tab_cv, tab_q, tab_rej = st.tabs(["📄 Xử lý một CV", "💬 Câu hỏi phỏng vấn theo JD", "📉 Lý do rớt phổ biến"])

with tab_cv:
    positions = {p["title"]: p for p in meta["positions"]}
    c1, c2 = st.columns([1.2, 1])
    with c1:
        titles = list(positions)
        default_pos = next((i for i, t in enumerate(titles) if "Data Analyst" in t), 0)
        pos_title = st.selectbox("Đối chiếu với vị trí (JD)", titles, index=default_pos)
        upload = st.file_uploader("Tải lên CV (PDF, DOCX, TXT)", type=["pdf", "docx", "txt", "md"])
        samples = sorted(p.name for p in SAMPLE_DIR.glob("*")) if SAMPLE_DIR.exists() else []
        sample = st.selectbox("…hoặc chọn CV mẫu có sẵn", ["(không)"] + samples)
    with c2:
        pos = positions[pos_title]
        st.markdown(f"**Yêu cầu bắt buộc:** {ui.chips(pos['required_skills'])}", unsafe_allow_html=True)
        st.markdown(f"**Ưu tiên:** {ui.chips(pos['nice_to_have_skills'])}", unsafe_allow_html=True)
        with st.expander("Mô tả công việc"):
            st.write(pos["jd_text"])
    if st.button("Phân tích CV", type="primary", disabled=not (upload or sample != "(không)")):
        if upload:
            name, data = upload.name, upload.getvalue()
        else:
            name, data = sample, (SAMPLE_DIR / sample).read_bytes()
        with st.spinner("Đang trích văn bản, ẩn danh và phân tích…"):
            try:
                st.session_state["last_cv_insight"] = api.post(
                    "/ai/analyze-cv-file", files={"file": (name, data)}, data={"position_id": str(pos["id"])})
            except api.ApiError as exc:
                ui.show_error(exc)
    if st.session_state.get("last_cv_insight"):
        ins = st.session_state["last_cv_insight"]
        st.divider()
        st.markdown(f"**Kết quả – {ins['subject']}** (mã nhận xét #{ins['id']})")
        ui.render_insight(ins)

with tab_q:
    st.write("Chọn hồ sơ đang xử lý để AI soạn bộ câu hỏi phỏng vấn có cấu trúc, gắn với JD và các điểm cần làm rõ.")
    try:
        active = api.get("/applications", params={"status": "active", "page_size": 500})["items"]
    except api.ApiError as exc:
        ui.show_error(exc)
        active = []
    options = {f"{a['application_code']} · {a['candidate']['display_name']} · {a['position']['title']} "
               f"({a['current_stage_name']})": a["id"] for a in active}
    choice = st.selectbox("Hồ sơ", list(options)) if options else None
    if choice and st.button("Soạn câu hỏi phỏng vấn", type="primary"):
        with st.spinner("AI đang soạn câu hỏi…"):
            try:
                st.session_state["last_questions"] = api.post(f"/ai/applications/{options[choice]}/interview-questions")
            except api.ApiError as exc:
                ui.show_error(exc)
    if st.session_state.get("last_questions"):
        st.divider()
        ui.render_insight(st.session_state["last_questions"])

with tab_rej:
    st.write("Tổng hợp & phân nhóm lý do ứng viên bị loại hoặc tự rút hồ sơ (NLP), kèm nhận định và đề xuất cải tiến.")
    pos_opts = {"Tất cả vị trí": None} | {p["title"]: p["id"] for p in meta["positions"]}
    pos_choice = st.selectbox("Phạm vi", list(pos_opts), key="rej_scope")
    if st.button("Phân tích lý do rớt", type="primary"):
        with st.spinner("Đang phân tích…"):
            try:
                st.session_state["last_rejection"] = api.post("/ai/rejection-insights",
                                                              json={"position_id": pos_opts[pos_choice]})
            except api.ApiError as exc:
                ui.show_error(exc)
    if st.session_state.get("last_rejection"):
        st.divider()
        ui.render_insight(st.session_state["last_rejection"])
