# =============================================================
# RESEARCH INFO / PROFILE PAGE
# Author: Aakash Kushwah
# =============================================================

import streamlit as st
import pandas as pd
from datetime import date
from database.connection import get_connection
from ui.session_controls import render_logout_button


COUNTRY_OPTIONS = [
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "Germany",
    "France",
    "Singapore",
    "United Arab Emirates",
    "Other",
]

OCCUPATION_OPTIONS = [
    "Working for Others",
    "Working for Self",
    "Student",
    "Homemaker",
    "Seeking Work",
    "Retired",
    "Other",
]


def get_users_table_columns(conn) -> set[str]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users'
        """
    )
    columns = {row[0] for row in cursor.fetchall()}
    cursor.close()
    return columns


def optional_user_column_expr(column_name: str, available_columns: set[str]) -> str:
    if column_name in available_columns:
        return column_name
    return f"NULL AS {column_name}"


def build_select_options(options: list[str], current_value) -> list[str]:
    normalized_current = (str(current_value).strip() if pd.notnull(current_value) else "")
    if normalized_current and normalized_current not in options:
        return [normalized_current] + options
    return options

# -------------------------------------------------------------
# SESSION CHECK
# -------------------------------------------------------------
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Please login first.")
    st.stop()

user_id = st.session_state.get("user_id")
username = st.session_state.get("username")

st.title("👤 User Profile & Research Info")
render_logout_button()

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
user_columns = get_users_table_columns(conn)

df_user = pd.read_sql("""
    SELECT username,
           {date_of_birth_expr},
           {gender_expr},
           {country_expr},
           {occupation_expr},
           created_at
    FROM users
    WHERE user_id = %s
""".format(
    date_of_birth_expr=optional_user_column_expr("date_of_birth", user_columns),
    gender_expr=optional_user_column_expr("gender", user_columns),
    country_expr=optional_user_column_expr("country", user_columns),
    occupation_expr=optional_user_column_expr("occupation", user_columns),
), conn, params=(user_id,))

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
        dob_input = (
            st.date_input(
                "Date of Birth",
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                value=date(2000, 1, 1)
            )
            if "dob" in missing_fields else dob
        )

        gender_input = (
            st.selectbox("Gender", ["Male", "Female", "Other"])
            if "gender" in missing_fields else user_data["gender"]
        )

        country_input = (
            st.selectbox(
                "Country",
                build_select_options(COUNTRY_OPTIONS, user_data["country"]),
            )
            if "country" in missing_fields else user_data["country"]
        )

        occupation_input = (
            st.selectbox(
                "Occupation",
                build_select_options(OCCUPATION_OPTIONS, user_data["occupation"]),
            )
            if "occupation" in missing_fields else user_data["occupation"]
        )

        submitted = st.form_submit_button("Save")

        if submitted:
            try:
                cursor = conn.cursor()
                update_fields = []
                update_values = []

                if "date_of_birth" in user_columns:
                    update_fields.append("date_of_birth = %s")
                    update_values.append(dob_input)
                if "gender" in user_columns:
                    update_fields.append("gender = %s")
                    update_values.append(gender_input)
                if "country" in user_columns:
                    update_fields.append("country = %s")
                    update_values.append(country_input)
                if "occupation" in user_columns:
                    update_fields.append("occupation = %s")
                    update_values.append(occupation_input)

                if not update_fields:
                    st.error("Profile fields are not available in the current database schema.")
                    cursor.close()
                    st.stop()

                update_values.append(user_id)
                cursor.execute(f"""
                    UPDATE users
                    SET {", ".join(update_fields)}
                    WHERE user_id = %s
                """, tuple(update_values))

                conn.commit()
                cursor.close()
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
