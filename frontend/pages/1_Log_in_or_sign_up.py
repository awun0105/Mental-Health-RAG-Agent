"""Unified authentication page for Google OAuth and local password fallback."""

from __future__ import annotations

import streamlit as st
from api_client import BackendError, get_google_oauth_url, login, register

st.title("Log in or sign up")
st.caption(
    "Google is the primary sign-in path. Local email/password remains available "
    "for development and password-based patient accounts.",
)


if st.session_state.get("access_token") and st.session_state.get("user"):
    user = st.session_state["user"]
    st.success(
        f"Signed in as **{user['email']}** with role `{user['role']}`.",
    )
    if user.get("role") == "admin":
        st.info("Admin role is active for this session.")
    if st.button("Log out"):
        st.session_state.pop("access_token", None)
        st.session_state.pop("user", None)
        st.rerun()
    st.stop()

st.subheader("Continue with Google")
st.write(
    "Use this for Google OAuth and admin bootstrap via `ADMIN_BOOTSTRAP_EMAILS`.",
)

if not st.session_state.get("google_oauth_url"):
    try:
        fetched_oauth_url = get_google_oauth_url()
    except BackendError as exc:
        st.error(f"Backend error {exc.status_code}: {exc}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Cannot connect to backend: {exc}")
    else:
        st.session_state["google_oauth_url"] = fetched_oauth_url
        st.rerun()

stored_oauth_url = st.session_state.get("google_oauth_url")
if isinstance(stored_oauth_url, str) and stored_oauth_url:
    st.link_button(
        "Continue with Google",
        stored_oauth_url,
        type="primary",
        use_container_width=True,
    )
elif st.button("Retry Google sign-in setup", use_container_width=True):
    st.session_state.pop("google_oauth_url", None)
    st.rerun()

st.divider()
st.subheader("Email and password")
st.caption(
    "Password sign-up creates a patient account. Doctor/admin accounts should be "
    "provisioned by an admin or bootstrapped through Google OAuth.",
)

login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

with login_tab:
    with st.form("password_login_form", clear_on_submit=False):
        email = st.text_input("Email", key="password_login_email")
        password = st.text_input("Password", type="password", key="password_login_password")
        submitted = st.form_submit_button("Log in with password")

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.")
        else:
            try:
                body = login(email=email, password=password)
            except BackendError as exc:
                if exc.status_code == 401:
                    st.error("Email or password is incorrect.")
                else:
                    st.error(f"Backend error {exc.status_code}: {exc}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Cannot connect to backend: {exc}")
            else:
                st.session_state["access_token"] = body["access_token"]
                st.session_state["user"] = body["user"]
                st.success(
                    f"Signed in as **{body['user']['email']}** with role `{body['user']['role']}`.",
                )
                st.rerun()

with signup_tab:
    with st.form("password_signup_form", clear_on_submit=False):
        signup_email = st.text_input("Email", key="password_signup_email")
        full_name = st.text_input("Full name")
        signup_password = st.text_input(
            "Password (at least 8 characters)",
            type="password",
            help="Password must be 8 to 128 characters.",
        )
        signup_submitted = st.form_submit_button("Create password account")

    if signup_submitted:
        if not signup_email or not full_name or not signup_password:
            st.error("Please fill in email, full name, and password.")
        elif len(signup_password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            try:
                user = register(
                    email=signup_email,
                    password=signup_password,
                    full_name=full_name,
                )
            except BackendError as exc:
                if exc.status_code == 409:
                    st.error("This email already exists. Log in instead.")
                elif exc.status_code == 422:
                    st.error(f"Invalid input: {exc}")
                else:
                    st.error(f"Backend error {exc.status_code}: {exc}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Cannot connect to backend: {exc}")
            else:
                st.success(
                    f"Created **{user['email']}** with role `{user['role']}`. "
                    "Use the Log in tab to continue.",
                )
