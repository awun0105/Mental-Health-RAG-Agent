"""Consent management — show current status, accept a policy version."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api_client import BackendError, accept_consent, consent_status

st.title("Chính sách & Đồng ý sử dụng")

if not st.session_state.get("access_token"):
    st.warning("Bạn cần đăng nhập trước. Mở trang **Log in or sign up**.")
    st.stop()

status: dict[str, Any] | None = None
try:
    status = consent_status()
except BackendError as exc:
    st.error(f"Lỗi đọc trạng thái consent ({exc.status_code}): {exc}")
except Exception as exc:  # noqa: BLE001
    st.error(f"Không kết nối được backend: {exc}")

current_policy_version = "v1"
if status is not None:
    current_policy_version = status["current_policy_version"]
    st.write("**Phiên bản hiện hành:**", f"`{current_policy_version}`")
    if status["has_valid_consent"]:
        st.success("Bạn đã chấp nhận phiên bản hiện hành.")
    else:
        st.warning("Bạn chưa chấp nhận phiên bản hiện hành.")

    latest = status.get("latest_accepted_policy_version")
    if latest:
        st.caption(f"Phiên bản đã chấp nhận gần nhất: `{latest}`.")
    else:
        st.caption("Bạn chưa từng chấp nhận phiên bản nào trước đây.")

st.markdown("---")
st.subheader("Chấp nhận chính sách")

with st.form("accept_consent_form"):
    policy_version = st.text_input(
        "Policy version cần chấp nhận",
        value=current_policy_version,
    )
    confirm = st.checkbox(
        "Tôi đã đọc và đồng ý với chính sách phiên bản này.",
    )
    submitted = st.form_submit_button("Ghi nhận đồng ý")

if submitted:
    if not policy_version:
        st.error("Vui lòng nhập policy version.")
    elif not confirm:
        st.error("Vui lòng tick xác nhận trước khi gửi.")
    else:
        try:
            body = accept_consent(policy_version=policy_version)
        except BackendError as exc:
            st.error(f"Lỗi {exc.status_code}: {exc}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Không kết nối được backend: {exc}")
        else:
            st.success(
                f"Đã ghi nhận đồng ý phiên bản `{body['policy_version']}` lúc "
                f"{body['accepted_at']}.",
            )
