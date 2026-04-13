# =============================================================
# RESEARCH INFO / PROFILE PAGE
# Author: Aakash Kushwah
# =============================================================

import streamlit as st
import pandas as pd
from database.connection import get_connection

# -------------------------------------------------------------
# SESSION CHECK
# -------------------------------------------------------------
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Please login first.")
    st.stop()

user_id = st.session_state.get("user_id")
username = st.session_state.get("username")

st.title("👤 User Profile & Research Info")

# -------------------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------------------
conn = get_connection()

if conn is None:
    st.error("❌ Database connection failed.")
    st.stop()

# -------------------------------------------------------------
# LOAD USER INFO
# -------------------------------------------------------------
df_user = pd.read_sql("""
    SELECT username, age, gender, country, occupation, created_at
    FROM users
    WHERE user_id = %s
""", conn, params=(user_id,))

if df_user.empty:
    st.error("User not found.")
    st.stop()

user_data = df_user.iloc[0]

st.subheader("📋 Your Profile")

col1, col2 = st.columns(2)

with col1:
    st.write(f"**Username:** {user_data['username']}")
    st.write(f"**Age:** {user_data['age'] or 'Not provided'}")
    st.write(f"**Gender:** {user_data['gender'] or 'Not provided'}")

with col2:
    st.write(f"**Country:** {user_data['country'] or 'Not provided'}")
    st.write(f"**Occupation:** {user_data['occupation'] or 'Not provided'}")
    st.write(f"**Member Since:** {str(user_data['created_at'])[:10]}")

st.markdown("---")

# -------------------------------------------------------------
# LOAD ASSESSMENT HISTORY
# -------------------------------------------------------------
df_scores = pd.read_sql("""
    SELECT c.category_name, s.score_value, s.created_at
    FROM scores s
    JOIN categories c ON s.category_id = c.category_id
    WHERE s.user_id = %s
    ORDER BY s.created_at DESC
""", conn, params=(user_id,))

st.subheader("📊 Assessment History")

if df_scores.empty:
    st.info("No assessment records found yet.")
else:
    st.dataframe(df_scores, use_container_width=True)

conn.close()

# -------------------------------------------------------------
# NAVIGATION
# -------------------------------------------------------------
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Go to Dashboard"):
        st.switch_page("pages/2_Dashboard.py")

with col2:
    if st.button("📝 Take Assessment"):
        st.switch_page("pages/3_Questionnaire.py")

st.caption("Built with ❤️ by Aakash Kushwah")