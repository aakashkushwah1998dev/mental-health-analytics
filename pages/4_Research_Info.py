# =============================================================
# RESEARCH INFO / PROFILE PAGE
# Author: Aakash Kushwah
# =============================================================

import streamlit as st
import pandas as pd
from datetime import date
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
    SELECT username, date_of_birth, gender, country, occupation, created_at
    FROM users
    WHERE user_id = %s
""", conn, params=(user_id,))

if df_user.empty:
    st.error("User not found.")
    st.stop()

user_data = df_user.iloc[0]

# -------------------------------------------------------------
# AGE CALCULATION
# -------------------------------------------------------------
def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

dob = user_data["date_of_birth"]
age = calculate_age(dob) if pd.notnull(dob) else None

# -------------------------------------------------------------
# PROFILE COMPLETION CHECK
# -------------------------------------------------------------
missing_fields = []

if pd.isnull(user_data["date_of_birth"]):
    missing_fields.append("dob")
if pd.isnull(user_data["gender"]):
    missing_fields.append("gender")
if pd.isnull(user_data["country"]):
    missing_fields.append("country")
if pd.isnull(user_data["occupation"]):
    missing_fields.append("occupation")

# -------------------------------------------------------------
# ASK USER TO COMPLETE PROFILE
# -------------------------------------------------------------
if missing_fields:
    st.warning("⚠️ Please complete your profile")

    with st.form("update_profile"):
        dob_input = st.date_input("Date of Birth") if "dob" in missing_fields else dob

        gender_input = (
            st.selectbox("Gender", ["Male", "Female", "Other"])
            if "gender" in missing_fields else user_data["gender"]
        )

        country_input = (
            st.text_input("Country")
            if "country" in missing_fields else user_data["country"]
        )

        occupation_input = (
            st.text_input("Occupation")
            if "occupation" in missing_fields else user_data["occupation"]
        )

        submitted = st.form_submit_button("Save")

        if submitted:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET date_of_birth = %s,
                        gender = %s,
                        country = %s,
                        occupation = %s
                    WHERE user_id = %s
                """, (dob_input, gender_input, country_input, occupation_input, user_id))

                conn.commit()
                st.success("✅ Profile updated successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error updating profile: {e}")

# -------------------------------------------------------------
# DISPLAY PROFILE
# -------------------------------------------------------------
st.subheader("📋 Your Profile")

col1, col2 = st.columns(2)

with col1:
    st.write(f"**Username:** {user_data['username']}")
    st.write(f"**Age:** {age if age else 'Not provided'}")
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