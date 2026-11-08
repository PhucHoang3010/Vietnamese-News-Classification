"""Kiểm duyệt nhận xét AI (human-in-the-loop): duyệt / chỉnh sửa / từ chối."""
import pandas as pd
import streamlit as st

import api
import ui

st.title("✅ Kiểm duyệt nhận xét AI")
st.caption("Mọi nội dung do AI tạo đều ở trạng thái **Chờ duyệt**. Quản lý tuyển dụng chỉ nhìn thấy nội dung đã được duyệt. "
           "Nội dung bị bộ lọc thiên vị gắn cờ cần chỉnh sửa hoặc ghi chú lý do trước khi duyệt.")

c1, c2 = st.columns(2)
status_map = {"Chờ duyệt": "pending_review", "Đã duyệt": "approved", "Đã từ chối": "rejected", "Tất cả": None}
type_map = {"Tất cả": None, "Tóm tắt CV": "cv_analysis", "Câu hỏi phỏng vấn": "interview_questions",
            "Lý do rớt phổ biến": "rejection_insights"}
status = c1.segmented_control("Trạng thái", list(status_map), default="Chờ duyệt")
kind = c2.selectbox("Loại nhận xét", list(type_map))
params = {k: v for k, v in {"status": status_map.get(status or "Tất cả"), "insight_type": type_map[kind]}.items() if v}
try:
    insights = api.get("/ai/insights", params=params)
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()

st.caption(f"{len(insights)} nhận xét")
if not insights:
    st.success("Không có nhận xét nào cần xử lý. 🎉")


def edit_form(ins: dict) -> dict | None:
    c = dict(ins["content"])
    kind = ins["insight_type"]
    if kind == "cv_analysis":
        c["headline"] = st.text_input("Tiêu đề", c.get("headline", ""), key=f"h{ins['id']}")
        c["summary"] = st.text_area("Tóm tắt", c.get("summary", ""), key=f"s{ins['id']}", height=120)
        c["highlights"] = [x for x in st.text_area("Điểm nổi bật (mỗi dòng một ý)", "\n".join(c.get("highlights", [])),
                                                   key=f"hl{ins['id']}").splitlines() if x.strip()]
        c["gaps"] = [x for x in st.text_area("Điểm cần làm rõ (mỗi dòng một ý)", "\n".join(c.get("gaps", [])),
                                             key=f"g{ins['id']}").splitlines() if x.strip()]
    elif kind == "interview_questions":
        df = pd.DataFrame(c.get("questions", []))
        edited = st.data_editor(df, num_rows="dynamic", key=f"q{ins['id']}", width="stretch")
        c["questions"] = edited.fillna("").to_dict(orient="records")
    elif kind == "rejection_insights":
        c["overview"] = st.text_area("Nhận định tổng quan", c.get("overview", ""), key=f"o{ins['id']}")
        c["actions"] = [x for x in st.text_area("Hành động đề xuất (mỗi dòng một ý)", "\n".join(c.get("actions", [])),
                                                key=f"a{ins['id']}").splitlines() if x.strip()]
    return c


for idx, ins in enumerate(insights):
    flag = " ⚠️" if ins["bias_flags"] else ""
    title = f"#{ins['id']} · {ins['type_label']} · {ins['subject'] or ins['position'] or 'Toàn công ty'}{flag}"
    with st.expander(title, expanded=idx == 0):
        ui.render_insight(ins)
        if ins["status"] == "pending_review" and ui.can("ai:review"):
            st.markdown("---")
            editing = st.toggle("✏️ Chỉnh sửa nội dung trước khi duyệt", key=f"edit{ins['id']}")
            edited = edit_form(ins) if editing else None
            note = st.text_input("Ghi chú kiểm duyệt", key=f"note{ins['id']}",
                                 placeholder="Bắt buộc nếu nội dung bị gắn cờ thiên vị")
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Duyệt", key=f"ap{ins['id']}", type="primary", width="stretch"):
                try:
                    api.post(f"/ai/insights/{ins['id']}/review",
                             json={"action": "approve", "note": note or None, "edited_content": edited})
                    st.toast(f"Đã duyệt nhận xét #{ins['id']}")
                    st.rerun()
                except api.ApiError as exc:
                    ui.show_error(exc)
            if b2.button("Từ chối", key=f"rj{ins['id']}", width="stretch"):
                try:
                    api.post(f"/ai/insights/{ins['id']}/review", json={"action": "reject", "note": note or None})
                    st.toast(f"Đã từ chối nhận xét #{ins['id']}")
                    st.rerun()
                except api.ApiError as exc:
                    ui.show_error(exc)
        elif ins["status"] != "pending_review" and ui.can("ai:review"):
            if st.button("Mở lại để kiểm duyệt", key=f"re{ins['id']}"):
                api.post(f"/ai/insights/{ins['id']}/review", json={"action": "reopen", "note": "Mở lại"})
                st.rerun()
