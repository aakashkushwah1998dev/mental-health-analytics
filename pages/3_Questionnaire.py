# =============================================================
# QUESTIONNAIRE PAGE
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

st.title("📝 Mental Wellness Questionnaire")

# -------------------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------------------
conn = get_connection()

if conn is None:
    st.error("❌ Database connection failed.")
    st.stop()

cursor = conn.cursor()

# -------------------------------------------------------------
# LOAD QUESTIONS
# -------------------------------------------------------------
df = pd.read_sql("""
    SELECT q.question_id, q.question_text, c.category_name, c.category_id
    FROM questions q
    JOIN categories c ON q.category_id = c.category_id
    ORDER BY c.category_name, q.question_id
""", conn)

if df.empty:
    st.error("❌ No questions found in the database.")
    st.stop()

# -------------------------------------------------------------
# RESPONSE SCALE
# -------------------------------------------------------------
options = {
    "Not at all": 0,
    "Several days": 1,
    "More than half the days": 2,
    "Nearly every day": 3
}

responses = {}

# -------------------------------------------------------------
# DISPLAY QUESTIONS GROUPED BY CATEGORY
# -------------------------------------------------------------
for category in df["category_name"].unique():

    st.subheader(f"📌 {category}")

    category_df = df[df["category_name"] == category]

    for _, row in category_df.iterrows():

        q_id = row["question_id"]

        answer = st.radio(
            label=row["question_text"],
            options=list(options.keys()),
            key=f"{category}_{q_id}"
        )

        responses[q_id] = options[answer]

# -------------------------------------------------------------
# SUBMIT BUTTON
# -------------------------------------------------------------
st.markdown("---")

if st.button("✅ Submit Assessment"):

    # ----------------------------------------------------------
    # CLEAR OLD RESPONSES AND SCORES FOR THIS USER
    # ----------------------------------------------------------
    cursor.execute("DELETE FROM responses WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM scores WHERE user_id = %s", (user_id,))

    # ----------------------------------------------------------
    # SAVE RAW RESPONSES
    # ----------------------------------------------------------
    for q_id, value in responses.items():
        cursor.execute("""
            INSERT INTO responses (user_id, question_id, answer_value)
            VALUES (%s, %s, %s)
        """, (user_id, q_id, value))

    conn.commit()

    # ----------------------------------------------------------
    # CALCULATE AND SAVE CATEGORY SCORES
    # ----------------------------------------------------------
    for category in df["category_name"].unique():

        category_df = df[df["category_name"] == category]
        total_score = sum(responses.get(row["question_id"], 0) for _, row in category_df.iterrows())

        # Get category_id
        cursor.execute(
            "SELECT category_id FROM categories WHERE category_name = %s",
            (category,)
        )

        result = cursor.fetchone()

        if result:
            category_id = result[0]
            cursor.execute("""
                INSERT INTO scores (user_id, category_id, score_value)
                VALUES (%s, %s, %s)
            """, (user_id, category_id, total_score))

    conn.commit()
    cursor.close()
    conn.close()

    st.success("✅ Assessment submitted successfully!")
    st.switch_page("pages/2_Dashboard.py")

# -------------------------------------------------------------
# FOOTER
# -------------------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ by Aakash Kushwah")