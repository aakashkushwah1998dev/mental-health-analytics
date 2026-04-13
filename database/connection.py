# =============================================================
# DATABASE CONNECTION MODULE
# Author: Aakash Kushwah
# Purpose: Create a reusable PostgreSQL connection via Supabase
# =============================================================

import psycopg2
import streamlit as st


def get_connection():
    """
    Returns a new PostgreSQL database connection.
    Credentials are loaded from .streamlit/secrets.toml
    Returns None if connection fails.
    """

    try:
        conn = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"]
        )
        return conn

    except Exception as e:
        st.error("❌ Database connection failed.")
        st.write(e)
        return None