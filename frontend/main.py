"""Navigation shell for the Mental Health AI Platform Streamlit app."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api_client import BackendError, exchange_google_auth_code, health

st.set_page_config(
    page_title="Mental Health AI Platform",
    page_icon=":material/psychology:",
    layout="wide",
)


def _query_value(name: str) -> str | None:
    value = st.query_params.get(name)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _clear_session() -> None:
    st.session_state.pop("access_token", None)
    st.session_state.pop("user", None)
    st.session_state.pop("google_oauth_url", None)


def _handle_google_redirect() -> None:
    google_error = _query_value("google_error")
    auth_code = _query_value("auth_code")

    if google_error:
        st.session_state["auth_flash_error"] = google_error
        st.query_params.clear()
        st.rerun()

    if not auth_code:
        return

    try:
        body = exchange_google_auth_code(auth_code)
    except BackendError as exc:
        st.session_state["auth_flash_error"] = f"Google login failed ({exc.status_code}): {exc}"
        st.query_params.clear()
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.session_state["auth_flash_error"] = f"Cannot connect to backend: {exc}"
        st.query_params.clear()
        st.rerun()
    else:
        st.session_state["access_token"] = body["access_token"]
        st.session_state["user"] = body["user"]
        st.session_state.pop("google_oauth_url", None)
        st.session_state["auth_flash_success"] = (
            f"Signed in as {body['user']['email']} with role {body['user']['role']}."
        )
        st.query_params.clear()
        st.rerun()


_handle_google_redirect()

token = st.session_state.get("access_token")
user = st.session_state.get("user")

with st.sidebar:
    st.markdown("### Mental Health AI")
    if token and user:
        st.caption(f"{user['email']} · `{user['role']}`")
        if st.button("Log out", use_container_width=True):
            _clear_session()
            st.rerun()
    else:
        st.caption("Not signed in")

if "auth_flash_error" in st.session_state:
    st.error(st.session_state.pop("auth_flash_error"))
if "auth_flash_success" in st.session_state:
    st.success(st.session_state.pop("auth_flash_success"))

pages: list[Any] = []

if not token or not user:
    pages.append(
        st.Page(
            "pages/1_Log_in_or_sign_up.py",
            title="Log in or sign up",
            icon=":material/login:",
        ),
    )

if token and user:
    pages.extend(
        [
            st.Page(
                "pages/3_Consent.py",
                title="Consent",
                icon=":material/fact_check:",
            ),
            st.Page(
                "pages/4_Profile.py",
                title="Profile",
                icon=":material/person:",
            ),
        ],
    )


def home_page() -> None:
    st.title("Mental Health AI Platform")
    st.write(
        "Privacy-first, human-in-the-loop AI hỗ trợ sức khoẻ tinh thần. "
        "AI hỗ trợ ra quyết định, không thay thế bác sĩ.",
    )

    if token and user:
        st.success(
            f"Đã đăng nhập với tài khoản **{user['email']}** (vai trò: `{user['role']}`).",
        )
    else:
        st.info("Bạn chưa đăng nhập. Mở trang **Log in or sign up** để bắt đầu.")

    st.markdown("---")
    st.subheader("Hướng dẫn nhanh")
    st.markdown(
        """
1. **Log in or sign up** — đăng nhập bằng Google OAuth hoặc email/password.
2. **Consent** — chấp nhận chính sách hiện hành sau khi đăng nhập.
3. **Profile** — kiểm tra claims trả về từ `/auth/me`.
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
            except Exception as exc:  # noqa: BLE001
                st.error(f"Không kết nối được backend: {exc}")


pages.insert(
    0,
    st.Page(
        home_page,
        title="Home",
        icon=":material/home:",
        default=True,
    ),
)

navigation = st.navigation(pages)
navigation.run()
