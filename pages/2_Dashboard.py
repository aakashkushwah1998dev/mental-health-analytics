# =============================================================
# DASHBOARD PAGE
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

st.title("📊 Mental Wellness Dashboard")

# -------------------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------------------
conn = get_connection()

if conn is None:
    st.error("❌ Database connection failed.")
    st.stop()


# -------------------------------------------------------------
# SCORE INTERPRETATION FUNCTION
# -------------------------------------------------------------
def interpret_score(category: str, score: int) -> tuple:
    """
    Returns (level_label, emoji) based on category and score.
    """

    if category == "PHQ9":
        if score <= 4:   return "Minimal", "🟢"
        elif score <= 9:  return "Mild", "🟡"
        elif score <= 14: return "Moderate", "🟠"
        elif score <= 19: return "Moderately Severe", "🔴"
        else:             return "Severe", "🔴"

    elif category == "GAD7":
        if score <= 4:   return "Minimal", "🟢"
        elif score <= 9:  return "Mild", "🟡"
        elif score <= 14: return "Moderate", "🟠"
        else:             return "Severe", "🔴"

    else:
        if score < 5:    return "Low", "🟢"
        elif score < 10: return "Moderate", "🟡"
        else:            return "High Risk", "🔴"


# -------------------------------------------------------------
# CHECK IF USER HAS TAKEN ASSESSMENT
# -------------------------------------------------------------
df_check = pd.read_sql(
    "SELECT COUNT(*) FROM responses WHERE user_id = %s",
    conn,
    params=(user_id,)
)

response_count = df_check.iloc[0, 0]

# -------------------------------------------------------------
# NEW USER — NO DATA YET
# -------------------------------------------------------------
if response_count == 0:

    st.subheader(f"Welcome, {username} 👋")
    st.info("You haven't taken the assessment yet. Let's get started!")

    if st.button("📝 Start Assessment"):
        st.switch_page("pages/3_Questionnaire.py")

# -------------------------------------------------------------
# RETURNING USER — SHOW DASHBOARD
# -------------------------------------------------------------
else:

    st.subheader(f"Welcome back, {username} 👋")

    # ----------------------------------------------------------
    # LOAD SCORES
    # ----------------------------------------------------------
    df_scores = pd.read_sql("""
        SELECT c.category_name, s.score_value
        FROM scores s
        JOIN categories c ON s.category_id = c.category_id
        WHERE s.user_id = %s
    """, conn, params=(user_id,))

    if df_scores.empty:
        st.warning("No scores found. Please take the assessment.")

    else:
        st.subheader("📊 Your Mental Health Scores")

        df_scores["Level"] = df_scores.apply(
            lambda x: interpret_score(x["category_name"], x["score_value"])[0],
            axis=1
        )

        df_scores["Status"] = df_scores.apply(
            lambda x: interpret_score(x["category_name"], x["score_value"])[1],
            axis=1
        )

        st.dataframe(df_scores, use_container_width=True)

        st.subheader("📈 Score Overview")
        st.bar_chart(df_scores.set_index("category_name")["score_value"])

    # ----------------------------------------------------------
    # TRENDS
    # ----------------------------------------------------------
    df_trend = pd.read_sql("""
        SELECT c.category_name, s.score_value, s.created_at
        FROM scores s
        JOIN categories c ON s.category_id = c.category_id
        WHERE s.user_id = %s
        ORDER BY s.created_at
    """, conn, params=(user_id,))

    if not df_trend.empty:

        st.subheader("📉 Mental Health Trends Over Time")

        df_trend["created_at"] = pd.to_datetime(df_trend["created_at"])

        pivot_df = df_trend.pivot(
            index="created_at",
            columns="category_name",
            values="score_value"
        )

        st.line_chart(pivot_df)

    # ----------------------------------------------------------
    # PERSONALIZED RECOMMENDATIONS
    # ----------------------------------------------------------
    if not df_scores.empty:

        st.subheader("💡 Personalized Recommendations")

        for _, row in df_scores.iterrows():

            category = row["category_name"]
            score = row["score_value"]
            level, emoji = interpret_score(category, score)

            st.write(f"**{category} → {level} {emoji}**")

            if level in ["Moderate", "Moderately Severe", "Severe", "High Risk"]:
                st.warning(
                    "Consider journaling, mindfulness exercises, or speaking with a therapist."
                )
            else:
                st.success("You're doing well. Keep up your healthy habits 🌿")

    # ----------------------------------------------------------
    # RETAKE ASSESSMENT
    # ----------------------------------------------------------
    st.markdown("---")

    if st.button("🔄 Retake Assessment"):
        st.switch_page("pages/3_Questionnaire.py")

conn.close()

# -------------------------------------------------------------
# FOOTER
# -------------------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ by Aakash Kushwah")