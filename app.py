# =============================================================
# MENTAL WELLNESS APP — MAIN ENTRY POINT
# Author: Aakash Kushwah
# =============================================================

import streamlit as st
import os
import subprocess


def get_build_version() -> str:
    env_sha = (
        os.getenv("STREAMLIT_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or os.getenv("RENDER_GIT_COMMIT")
    )
    if env_sha:
        return env_sha[:7]

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"

# -------------------------------------------------------------
# PAGE CONFIGURATION (must be first Streamlit command)
# -------------------------------------------------------------
st.set_page_config(
    page_title="Mental Wellness App",
    page_icon="🧠",
    layout="wide"
)

# -------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

# -------------------------------------------------------------
# MAIN LANDING PAGE
# -------------------------------------------------------------
st.title("🧠 Mental Wellness System")

st.markdown("""
Welcome to your **AI-powered Mental Wellness Platform** 💚

This system helps you:
- Understand your mental health
- Track your emotional patterns
- Get personalized recommendations
""")

st.markdown("---")

# -------------------------------------------------------------
# LOGIN / LOGGED IN FLOW
# -------------------------------------------------------------
if not st.session_state.logged_in:

    st.warning("⚠️ Please login to continue.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔐 Login / Register"):
            st.switch_page("pages/1_Login.py")

    with col2:
        st.info("New users can register directly from the login page.")

else:

    st.success(f"Welcome back, **{st.session_state.username}** 👋")

    # ------------------ LOGOUT BUTTON ------------------
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.success("Logged out successfully!")
        st.switch_page("pages/1_Login.py")

    st.markdown("### 🚀 Go to Dashboard")

    if st.button("📊 Open Dashboard"):
        st.switch_page("pages/2_Dashboard.py")

    st.markdown("---")

    st.markdown("### ⚡ Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 Take Assessment"):
            st.switch_page("pages/3_Questionnaire.py")

    with col2:
        if st.button("👤 View Profile"):
            st.switch_page("pages/4_Research_Info.py")

# -------------------------------------------------------------
# FOOTER
# -------------------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ by Aakash Kushwah")
st.caption(f"Build version: `{get_build_version()}`")