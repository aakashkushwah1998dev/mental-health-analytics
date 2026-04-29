# =============================================================
# QUESTIONNAIRE PAGE
# Author: Aakash Kushwah
# =============================================================

import streamlit as st
import pandas as pd
from database.connection import get_connection
from src.services.scoring import QuestionScore, compute_category_total
from ui.session_controls import render_logout_button


def load_questions(conn):
    """
    Load questionnaire rows while remaining compatible with databases
    that do not yet have the questions.is_reversed column.
    """

    schema_cursor = conn.cursor()
    schema_cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'questions'
              AND column_name = 'is_reversed'
        )
        """
    )
    has_is_reversed = schema_cursor.fetchone()[0]
    schema_cursor.close()

    reversed_column_sql = "q.is_reversed" if has_is_reversed else "FALSE AS is_reversed"

    df = pd.read_sql(
        f"""
        SELECT q.question_id, q.question_text, {reversed_column_sql},
               c.category_name, c.category_id
        FROM questions q
        JOIN categories c ON q.category_id = c.category_id
        ORDER BY c.category_name, q.question_id
        """,
        conn,
    )
    return df, has_is_reversed

# -------------------------------------------------------------
# SESSION CHECK
# -------------------------------------------------------------
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Please login first.")
    st.stop()

user_id = st.session_state.get("user_id")
username = st.session_state.get("username")

st.title("📝 Mental Wellness Questionnaire")
render_logout_button()

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
df, has_is_reversed = load_questions(conn)

if df.empty:
    st.error("❌ No questions found in the database.")
    st.stop()

if not has_is_reversed:
    st.info("Reverse-scored question metadata is missing in this database, so default scoring is being used for now.")

st.caption(f"Please answer all {len(df)} questions and let us know how you are feeling before you submit.")

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
    # Ensure session user_id exists in DB (common after DB resets/migrations).
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    user_row = cursor.fetchone()
    if user_row is None and username:
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_row = cursor.fetchone()
        if user_row:
            user_id = user_row[0]
            st.session_state["user_id"] = user_id

    if user_row is None:
        st.error("Your account session is out of sync with the database. Please log in again.")
        cursor.close()
        conn.close()
        st.stop()

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
        category_rows = [
            QuestionScore(
                question_id=int(row["question_id"]),
                category_name=str(row["category_name"]),
                is_reversed=bool(row["is_reversed"]),
            )
            for _, row in category_df.iterrows()
        ]
        total_score = compute_category_total(category_rows, responses)

        # Get category_id
        cursor.execute(
            "SELECT category_id FROM categories WHERE category_name = %s",
            (category,)
        )

        result = cursor.fetchone()

        if result:
            category_id = result[0]
            # Avoid relying on a UNIQUE constraint for ON CONFLICT since some
            # Supabase databases may not have it applied yet.
            cursor.execute(
                """
                UPDATE scores
                SET score_value = %s,
                    user_id = %s
                WHERE attempt_id = %s AND category_id = %s
                """,
                (total_score, user_id, attempt_id, category_id),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    INSERT INTO scores (user_id, category_id, score_value, attempt_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_id, category_id, total_score, attempt_id),
                )

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
