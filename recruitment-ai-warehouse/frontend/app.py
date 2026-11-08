"""TalentLens – giao diện web Streamlit (đăng nhập + điều hướng theo vai trò)."""
from __future__ import annotations

import streamlit as st

import api
import ui

st.set_page_config(page_title="TalentLens – Kho dữ liệu tuyển dụng AI", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")
ui.inject_css()

DEMO_ACCOUNTS = [("hr.lan", "Demo@123", "HR – xem toàn bộ, có thông tin cá nhân"),
                 ("manager.data", "Demo@123", "Quản lý khối Dữ liệu & AI – dữ liệu đã che"),
                 ("manager.tech", "Demo@123", "Quản lý khối Công nghệ"),
                 ("admin", "Admin@123", "Quản trị hệ thống – quản lý người dùng")]


def login_page() -> None:
    left, mid, right = st.columns([1, 1.25, 1])
    with mid:
        st.markdown("<div style='height:4vh'></div>", unsafe_allow_html=True)
        st.markdown("## 📊 TalentLens")
        st.markdown("**Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên**")
        st.caption("ETL đa nguồn → Kho dữ liệu PostgreSQL → Dashboard pipeline → AI tóm tắt CV, có kiểm duyệt & chống thiên vị")
        with st.form("login", border=True):
            username = st.text_input("Tên đăng nhập", placeholder="vd: hr.lan")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập", type="primary", width="stretch")
        if submitted:
            if not username or not password:
                st.warning("Vui lòng nhập tên đăng nhập và mật khẩu.")
            else:
                with st.spinner("Đang đăng nhập… (lần đầu có thể mất ~1 phút nếu máy chủ đang khởi động)"):
                    try:
                        api.login(username, password)
                        st.rerun()
                    except api.ApiError as exc:
                        st.error(str(exc))
        with st.expander("Tài khoản demo"):
            for u, p, note in DEMO_ACCOUNTS:
                st.markdown(f"`{u}` / `{p}` – {note}")


def sidebar() -> None:
    user = ui.user()
    with st.sidebar:
        st.markdown("<div class='tl-brand'>📊 TalentLens</div><div class='tl-sub'>Kho dữ liệu tuyển dụng AI</div>",
                    unsafe_allow_html=True)
        st.divider()
        st.markdown(f"**{user.get('full_name')}**")
        st.caption(f"{user.get('role_label')}" + (f" · {user['department']}" if user.get("department") else ""))
        try:
            ai = api.meta().get("ai", {})
            st.caption(("🤖 AI: Claude · " + ai.get("model", "")) if ai.get("provider") == "claude"
                       else "🤖 AI: engine NLP nội bộ (chưa cấu hình Claude API key)")
        except Exception:  # noqa: BLE001
            pass
        if st.button("Đăng xuất", width="stretch"):
            st.session_state.clear()
            st.rerun()


if "token" not in st.session_state:
    st.navigation([st.Page(login_page, title="Đăng nhập", icon="🔐")], position="hidden").run()
else:
    sidebar()
    analysis = [st.Page("views/dashboard.py", title="Tổng quan pipeline", icon="📈", default=True),
                st.Page("views/candidates.py", title="Ứng viên & hồ sơ", icon="👥"),
                st.Page("views/reports.py", title="Báo cáo tuần", icon="📝")]
    ai_pages = []
    if ui.can("ai:run"):
        ai_pages.append(st.Page("views/ai_studio.py", title="AI phân tích CV", icon="🤖"))
    if ui.can("ai:review"):
        ai_pages.append(st.Page("views/review.py", title="Kiểm duyệt nhận xét AI", icon="✅"))
    if ui.can("fairness:read"):
        ai_pages.append(st.Page("views/fairness.py", title="Giám sát công bằng", icon="⚖️"))
    admin_pages = []
    if ui.can("etl:run"):
        admin_pages.append(st.Page("views/etl.py", title="Nhập dữ liệu (ETL)", icon="📥"))
    if ui.can("users:manage"):
        admin_pages.append(st.Page("views/users.py", title="Quản lý người dùng", icon="🔐"))
    if ui.can("audit:read"):
        admin_pages.append(st.Page("views/audit.py", title="Nhật ký hệ thống", icon="🧾"))
    admin_pages.append(st.Page("views/account.py", title="Tài khoản của tôi", icon="👤"))
    pages = {"Phân tích": analysis}
    if ai_pages:
        pages["AI & Chống thiên vị"] = ai_pages
    pages["Dữ liệu & Quản trị"] = admin_pages
    st.navigation(pages).run()
