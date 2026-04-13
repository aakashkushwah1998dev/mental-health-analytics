# =============================================================
# AUTHENTICATION SERVICE
# Author: Aakash Kushwah
# Purpose: Handle login and auto-registration in one flow
# =============================================================

import streamlit as st
from database.connection import get_connection


def login_or_register(username: str, password: str) -> str:
    """
    Handles both login and registration.

    - If user exists → validates password → logs in
    - If user does not exist → creates account → logs in

    Returns:
        "login_success"    → credentials matched
        "register_success" → new account created
        "login_failed"     → wrong password
        "error"            → database issue
    """

    conn = get_connection()

    if conn is None:
        return "error"

    cursor = conn.cursor()

    # ----------------------------------------------------------
    # CHECK IF USER EXISTS
    # ----------------------------------------------------------
    cursor.execute(
        "SELECT user_id, password FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()

    # ----------------------------------------------------------
    # LOGIN FLOW
    # ----------------------------------------------------------
    if user:

        user_id, stored_password = user

        if password == stored_password:

            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user_id
            st.session_state["username"] = username

            cursor.close()
            conn.close()

            return "login_success"

        else:
            cursor.close()
            conn.close()
            return "login_failed"

    # ----------------------------------------------------------
    # REGISTER FLOW
    # ----------------------------------------------------------
    else:

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING user_id",
            (username, password)
        )

        new_user_id = cursor.fetchone()[0]
        conn.commit()

        st.session_state["logged_in"] = True
        st.session_state["user_id"] = new_user_id
        st.session_state["username"] = username

        cursor.close()
        conn.close()

        return "register_success"