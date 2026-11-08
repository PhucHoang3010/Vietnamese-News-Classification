"""Quản lý người dùng & phân quyền (chỉ Admin)."""
import pandas as pd
import streamlit as st

import api
import ui

st.title("🔐 Quản lý người dùng")
meta = api.meta()
roles = meta["roles"]
depts = {d["name"]: d["id"] for d in meta["departments"]}

try:
    users = api.get("/users")
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()

st.dataframe(pd.DataFrame([{"ID": u["id"], "Tên đăng nhập": u["username"], "Họ tên": u["full_name"],
                            "Vai trò": u["role_label"], "Phòng ban": u["department"] or "–",
                            "Hoạt động": "✅" if u["is_active"] else "⛔",
                            "Đăng nhập gần nhất": ui.fmt_dt(u["last_login_at"], True)} for u in users]),
             hide_index=True, width="stretch")

with st.expander("Ma trận phân quyền"):
    st.markdown("""
| Chức năng | Admin | HR | Quản lý tuyển dụng |
|---|:-:|:-:|:-:|
| Xem dashboard | Toàn công ty | Toàn công ty | Chỉ phòng ban mình |
| Xem thông tin cá nhân ứng viên | ✅ | ✅ | ⛔ (đã che) |
| Chạy ETL / nhập dữ liệu | ✅ | ✅ | ⛔ |
| Chạy AI phân tích | ✅ | ✅ | ⛔ |
| Kiểm duyệt nhận xét AI | ✅ | ✅ | ⛔ (chỉ xem bản đã duyệt) |
| Ghi nhận kết quả phỏng vấn | ✅ | ✅ | ✅ (phòng ban mình) |
| Báo cáo tuần | Tạo/duyệt | Tạo/duyệt | Xem bản đã duyệt |
| Giám sát công bằng | ✅ | ✅ | ⛔ |
| Quản lý người dùng, nhật ký | ✅ | ⛔ | ⛔ |
""")

left, right = st.columns(2)
with left, st.form("create_user", border=True):
    st.markdown("**Thêm người dùng**")
    username = st.text_input("Tên đăng nhập")
    full_name = st.text_input("Họ tên")
    email = st.text_input("Email")
    role = st.selectbox("Vai trò", list(roles), format_func=roles.get)
    dept = st.selectbox("Phòng ban", ["(không)"] + list(depts))
    password = st.text_input("Mật khẩu ban đầu (≥ 8 ký tự)", type="password")
    if st.form_submit_button("Tạo tài khoản", type="primary"):
        try:
            api.post("/users", json={"username": username, "full_name": full_name, "email": email or None,
                                     "role": role, "department_id": depts.get(dept), "password": password})
            st.success("Đã tạo tài khoản.")
            st.rerun()
        except api.ApiError as exc:
            ui.show_error(exc)

with right, st.container(border=True):
    st.markdown("**Cập nhật người dùng**")
    target = st.selectbox("Người dùng", users, format_func=lambda u: f"{u['username']} – {u['full_name']}")
    with st.form("update_user"):
        new_role = st.selectbox("Vai trò", list(roles), index=list(roles).index(target["role"]), format_func=roles.get)
        names = ["(không)"] + list(depts)
        cur = next((n for n, i in depts.items() if i == target["department_id"]), "(không)")
        new_dept = st.selectbox("Phòng ban", names, index=names.index(cur))
        active = st.checkbox("Đang hoạt động", value=target["is_active"])
        if st.form_submit_button("Lưu thay đổi"):
            try:
                api.patch(f"/users/{target['id']}", json={"role": new_role, "department_id": depts.get(new_dept),
                                                          "is_active": active})
                st.success("Đã cập nhật.")
                st.rerun()
            except api.ApiError as exc:
                ui.show_error(exc)
    with st.form("reset_pw"):
        pw = st.text_input("Đặt lại mật khẩu", type="password")
        if st.form_submit_button("Đặt lại mật khẩu"):
            try:
                api.post(f"/users/{target['id']}/reset-password", json={"new_password": pw})
                st.success("Đã đặt lại mật khẩu.")
            except api.ApiError as exc:
                ui.show_error(exc)
