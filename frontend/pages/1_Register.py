"""Register a new local email/password patient account.

Public self-registration is patient-only. Doctor and admin accounts are
provisioned by an administrator through privileged flows; the role is
fixed at the backend regardless of any value the form might send.
"""

from __future__ import annotations

import streamlit as st
from api_client import BackendError, register

st.set_page_config(page_title="Register", page_icon="🆕")
st.title("Đăng ký tài khoản")
st.caption(
    "Tài khoản tự đăng ký luôn có vai trò **patient**. "
    "Tài khoản **doctor** / **admin** do quản trị viên tạo riêng.",
)

with st.form("register_form", clear_on_submit=False):
    email = st.text_input("Email")
    full_name = st.text_input("Họ tên")
    password = st.text_input(
        "Mật khẩu (≥ 8 ký tự)",
        type="password",
        help="Mật khẩu phải có ít nhất 8 ký tự, tối đa 128 ký tự.",
    )
    submitted = st.form_submit_button("Đăng ký")

if submitted:
    if not email or not password or not full_name:
        st.error("Vui lòng điền đầy đủ Email / Họ tên / Mật khẩu.")
    elif len(password) < 8:
        st.error("Mật khẩu cần ít nhất 8 ký tự.")
    else:
        try:
            user = register(
                email=email,
                password=password,
                full_name=full_name,
            )
        except BackendError as exc:
            if exc.status_code == 409:
                st.error("Email này đã tồn tại. Hãy đăng nhập hoặc dùng email khác.")
            elif exc.status_code == 422:
                st.error(f"Dữ liệu không hợp lệ: {exc}")
            else:
                st.error(f"Lỗi {exc.status_code}: {exc}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Không kết nối được backend: {exc}")
        else:
            st.success(
                f"Tạo tài khoản thành công cho **{user['email']}** "
                f"(role: `{user['role']}`). Mời sang trang **Login**.",
            )
