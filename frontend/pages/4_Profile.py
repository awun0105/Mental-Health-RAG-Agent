"""Profile page — show the JWT claims returned by /auth/me."""

from __future__ import annotations

import streamlit as st
from api_client import BackendError, get_me

st.title("Hồ sơ tài khoản")

if not st.session_state.get("access_token"):
    st.warning("Bạn cần đăng nhập trước. Mở trang **Log in or sign up**.")
    st.stop()

try:
    claims = get_me()
except BackendError as exc:
    if exc.status_code == 401:
        st.error("Token đã hết hạn hoặc không hợp lệ. Hãy đăng nhập lại.")
        st.session_state.pop("access_token", None)
        st.session_state.pop("user", None)
    else:
        st.error(f"Lỗi {exc.status_code}: {exc}")
except Exception as exc:  # noqa: BLE001
    st.error(f"Không kết nối được backend: {exc}")
else:
    st.subheader("Claims từ /auth/me")
    st.json(claims)

    user = st.session_state.get("user")
    if user is not None:
        st.markdown("---")
        st.subheader("User payload từ login")
        st.json(user)
