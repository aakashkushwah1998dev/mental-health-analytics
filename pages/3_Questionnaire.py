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
    SELECT q.question_id, q.question_text, q.is_reversed,
           c.category_name, c.category_id
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
mood_label = st.selectbox(
    "How are you feeling right now?",
    ["Calm", "Neutral", "Stressed", "Anxious", "Low"],
    index=1
)

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
    cursor.execute(
        "SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM assessment_attempts WHERE user_id = %s",
        (user_id,)
    )
    attempt_number = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO assessment_attempts (user_id, attempt_number, mood_label)
        VALUES (%s, %s, %s)
        RETURNING attempt_id
        """,
        (user_id, attempt_number, mood_label)
    )
    attempt_id = cursor.fetchone()[0]

    # ----------------------------------------------------------
    # SAVE RAW RESPONSES
    # ----------------------------------------------------------
    for q_id, value in responses.items():
        cursor.execute("""
            INSERT INTO responses (user_id, question_id, answer_value, attempt_id)
            VALUES (%s, %s, %s, %s)
        """, (user_id, q_id, value, attempt_id))

    conn.commit()

    # ----------------------------------------------------------
    # CALCULATE AND SAVE CATEGORY SCORES
    # ----------------------------------------------------------
    for category in df["category_name"].unique():

        category_df = df[df["category_name"] == category]
        total_score = 0
        for _, row in category_df.iterrows():
            raw_value = responses.get(row["question_id"], 0)
            if row["is_reversed"]:
                score_value = 3 - raw_value
            else:
                score_value = raw_value
            total_score += score_value

        # Get category_id
        cursor.execute(
            "SELECT category_id FROM categories WHERE category_name = %s",
            (category,)
        )

        result = cursor.fetchone()

        if result:
            category_id = result[0]
            cursor.execute("""
                INSERT INTO scores (user_id, category_id, score_value, attempt_id)
                VALUES (%s, %s, %s, %s)
            """, (user_id, category_id, total_score, attempt_id))

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