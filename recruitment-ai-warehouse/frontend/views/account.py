"""Thông tin tài khoản & đổi mật khẩu."""
import streamlit as st

import api
import ui

st.title("👤 Tài khoản của tôi")
u = ui.user()
c1, c2 = st.columns(2)
with c1, st.container(border=True):
    st.markdown(f"**{u.get('full_name')}**  \n`{u.get('username')}` · {u.get('role_label')}  \n"
                f"Phòng ban: {u.get('department') or '–'}  \nEmail: {u.get('email') or '–'}")
    st.markdown("**Quyền được cấp**")
    st.markdown(ui.chips(u.get("permissions", [])), unsafe_allow_html=True)
with c2, st.form("pw", border=True):
    st.markdown("**Đổi mật khẩu**")
    cur = st.text_input("Mật khẩu hiện tại", type="password")
    new = st.text_input("Mật khẩu mới (≥ 8 ký tự)", type="password")
    again = st.text_input("Nhập lại mật khẩu mới", type="password")
    if st.form_submit_button("Cập nhật", type="primary"):
        if new != again:
            st.error("Mật khẩu nhập lại không khớp.")
        else:
            try:
                api.post("/auth/change-password", json={"current_password": cur, "new_password": new})
                st.success("Đã đổi mật khẩu.")
            except api.ApiError as exc:
                ui.show_error(exc)
