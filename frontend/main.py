"""Home page for the Mental Health AI Platform Streamlit app.

The app is multi-page: pages live under ``frontend/pages/`` and Streamlit
auto-discovers them in the sidebar.
"""

from __future__ import annotations

import streamlit as st
from api_client import BackendError, health

st.set_page_config(
    page_title="Mental Health AI Platform",
    page_icon="🧠",
    layout="wide",
)

st.title("Mental Health AI Platform")
st.write(
    "Privacy-first, human-in-the-loop AI hỗ trợ sức khoẻ tinh thần. "
    "AI hỗ trợ ra quyết định, không thay thế bác sĩ.",
)

token = st.session_state.get("access_token")
user = st.session_state.get("user")

if token and user:
    st.success(
        f"Đã đăng nhập với tài khoản **{user['email']}** (vai trò: `{user['role']}`).",
    )
    if st.button("Đăng xuất"):
        st.session_state.pop("access_token", None)
        st.session_state.pop("user", None)
        st.rerun()
else:
    st.info(
        "Bạn chưa đăng nhập. Mở trang **Login** hoặc **Register** ở sidebar để bắt đầu.",
    )

st.markdown("---")
st.subheader("Hướng dẫn nhanh")
st.markdown(
    """
1. **Register** — tạo tài khoản mới (email + mật khẩu).
2. **Login** — đăng nhập, token JWT được lưu vào session.
3. **Consent** — chấp nhận chính sách hiện hành (yêu cầu trước khi dùng tính năng AI).
4. **Profile** — kiểm tra claims trả về từ `/auth/me`.

Tính năng Google login sẽ được thêm sau khi backend Google OAuth được wire-up.
""".strip(),
)

with st.expander("Backend connectivity check"):
    if st.button("Check Backend Health"):
        try:
            data = health()
            st.success(f"Server status: {data['status']}")
            st.json(data)
        except BackendError as exc:
            st.error(f"Backend trả lỗi {exc.status_code}: {exc}")
        except Exception as exc:  # noqa: BLE001 — surface any network error to the user
            st.error(f"Không kết nối được backend: {exc}")
