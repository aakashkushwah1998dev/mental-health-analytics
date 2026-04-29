import streamlit as st


def logout_user(redirect_page: str = "pages/1_Login.py") -> None:
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    st.switch_page(redirect_page)


def render_logout_button() -> None:
    if not st.session_state.get("logged_in"):
        return

    with st.sidebar:
        st.markdown("### Session")
        username = st.session_state.get("username") or "User"
        st.caption(f"Signed in as `{username}`")

        if st.button("Logout", key="sidebar_logout"):
            logout_user()
