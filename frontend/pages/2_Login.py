"""Email + password login."""

from __future__ import annotations

import streamlit as st
from api_client import BackendError, login

st.set_page_config(page_title="Login", page_icon="🔑")
st.title("Đăng nhập")

if st.session_state.get("access_token") and st.session_state.get("user"):
    user = st.session_state["user"]
    st.success(
        f"Bạn đã đăng nhập với **{user['email']}** (`{user['role']}`). "
        "Có thể qua trang Consent hoặc Profile.",
    )
    if st.button("Đăng xuất"):
        st.session_state.pop("access_token", None)
        st.session_state.pop("user", None)
        st.rerun()
    st.stop()

with st.form("login_form", clear_on_submit=False):
    email = st.text_input("Email")
    password = st.text_input("Mật khẩu", type="password")
    submitted = st.form_submit_button("Đăng nhập")

if submitted:
    if not email or not password:
        st.error("Vui lòng điền Email và Mật khẩu.")
    else:
        try:
            body = login(email=email, password=password)
        except BackendError as exc:
            if exc.status_code == 401:
                st.error("Email hoặc mật khẩu không đúng.")
            else:
                st.error(f"Lỗi {exc.status_code}: {exc}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Không kết nối được backend: {exc}")
        else:
            st.session_state["access_token"] = body["access_token"]
            st.session_state["user"] = body["user"]
            st.success(
                f"Đăng nhập thành công: **{body['user']['email']}** "
                f"(role: `{body['user']['role']}`).",
            )
            st.info(
                "Mở trang **Consent** ở sidebar để chấp nhận chính sách, "
                "hoặc **Profile** để xem claims.",
            )
