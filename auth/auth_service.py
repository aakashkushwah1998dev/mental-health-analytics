import streamlit as st
from src.services.auth import login_or_register as login_or_register_service


def login_or_register(username: str, password: str) -> str:
    try:
        result = login_or_register_service(username, password)
    except Exception:
        return "error"

    if result.user_id is not None:
        st.session_state["logged_in"] = True
        st.session_state["user_id"] = result.user_id
        st.session_state["username"] = result.username

    return result.status