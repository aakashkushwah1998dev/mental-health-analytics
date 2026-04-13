# =============================================================
# DASHBOARD PAGE
# Author: Aakash Kushwah
# =============================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database.connection import get_connection

# -------------------------------------------------------------
# SESSION CHECK
# -------------------------------------------------------------
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Please login first.")
    st.stop()

user_id  = st.session_state.get("user_id")
username = st.session_state.get("username")

st.title("📊 Mental Wellness Dashboard")

# -------------------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------------------
conn = get_connection()
if conn is None:
    st.error("❌ Database connection failed.")
    st.stop()


# =============================================================
# SCORING INTERPRETATION
# Each category has its own validated range logic
# =============================================================
def interpret_score(category: str, score: int) -> tuple:
    """
    Returns (level_label, emoji, color_hex)
    Based on clinically validated scoring ranges.
    """

    cat = category.upper()

    # ── PHQ-9: Depression Screening ──────────────────────────
    # Range: 0–27 (9 questions × 0–3)
    # Higher = more depressive symptoms = worse
    if cat == "PHQ9":
        if score <= 4:   return "Minimal",           "🟢", "#2ecc71"
        elif score <= 9:  return "Mild",               "🟡", "#f1c40f"
        elif score <= 14: return "Moderate",           "🟠", "#e67e22"
        elif score <= 19: return "Moderately Severe",  "🔴", "#e74c3c"
        else:             return "Severe",             "🔴", "#c0392b"

    # ── GAD-7: Anxiety Screening ──────────────────────────────
    # Range: 0–21 (7 questions × 0–3)
    # Higher = more anxiety = worse
    elif cat == "GAD7":
        if score <= 4:   return "Minimal",   "🟢", "#2ecc71"
        elif score <= 9:  return "Mild",      "🟡", "#f1c40f"
        elif score <= 14: return "Moderate",  "🟠", "#e67e22"
        else:             return "Severe",    "🔴", "#e74c3c"

    # ── Rosenberg Self-Esteem Scale ───────────────────────────
    # Range: 0–30 (10 questions, mix of agree/disagree)
    # In your 0–3 scale version:
    # Lower raw score = lower self-esteem = worse
    elif cat == "ROSENBERG":
        if score >= 20:  return "High Self-Esteem",     "🟢", "#2ecc71"
        elif score >= 15: return "Normal Self-Esteem",   "🟡", "#f1c40f"
        elif score >= 10: return "Low Self-Esteem",      "🟠", "#e67e22"
        else:             return "Very Low Self-Esteem", "🔴", "#e74c3c"

    # ── Big Five Personality ──────────────────────────────────
    # Not a clinical risk scale — it's a personality inventory
    # We interpret it differently: no "good" or "bad" score
    # We show personality profile instead of risk level
    elif cat == "BIGFIVE":
        if score >= 20:  return "High Trait Expression",   "🔵", "#3498db"
        elif score >= 10: return "Moderate Trait Expression","🟡", "#f1c40f"
        else:             return "Low Trait Expression",    "🟤", "#95a5a6"

    # ── Generic fallback ─────────────────────────────────────
    else:
        if score <= 5:   return "Low",       "🟢", "#2ecc71"
        elif score <= 10: return "Moderate",  "🟡", "#f1c40f"
        else:             return "High Risk", "🔴", "#e74c3c"


# =============================================================
# RECOMMENDATIONS ENGINE
# Real, specific, actionable activities per category + level
# =============================================================
def get_recommendations(category: str, level: str) -> list:
    """
    Returns a list of specific, actionable recommendations
    based on category and severity level.
    """

    cat = category.upper()
    lvl = level.upper()

    recs = {

        # ── PHQ-9 Depression ──────────────────────────────────
        "PHQ9": {
            "MINIMAL": [
                "🌅 Start a 5-minute morning gratitude journal — write 3 things you're grateful for each day.",
                "🚶 Take a 20-minute walk outside daily — sunlight directly boosts serotonin levels.",
                "📞 Call or meet a friend at least once a week to maintain social connection.",
                "😴 Maintain a consistent sleep schedule — same bedtime and wake time every day.",
            ],
            "MILD": [
                "📔 Try structured journaling: write about what happened, how you felt, and one thing you'd do differently.",
                "🏃 Exercise 3x per week — even 30 minutes of brisk walking significantly reduces mild depression.",
                "🎨 Pick up a creative hobby: drawing, cooking, music, or writing — creative output lifts mood.",
                "🌿 Spend 20 minutes in nature daily — studies show it reduces cortisol and rumination.",
                "📵 Reduce social media to 30 minutes/day — passive scrolling worsens low mood.",
            ],
            "MODERATE": [
                "🧠 Begin Cognitive Behavioral Therapy (CBT) — consider BetterHelp, Wysa app, or a local therapist.",
                "📋 Use a mood tracking app (Daylio, Moodfit) to identify your triggers and patterns.",
                "🏋️ Commit to structured daily exercise — 45 minutes of moderate cardio 4x/week.",
                "🧘 Practice guided mindfulness meditation 10–15 min/day using Headspace or Insight Timer.",
                "👥 Join a support group — online or in-person — to reduce isolation.",
                "⚠️ Talk to a trusted person in your life about how you're feeling.",
            ],
            "MODERATELY SEVERE": [
                "🏥 Please consult a licensed mental health professional or psychiatrist — this level warrants clinical support.",
                "💊 A doctor may discuss medication options alongside therapy — this is nothing to fear.",
                "🆘 Save a crisis helpline in your phone: iCall India: 9152987821",
                "🛡️ Remove or limit access to things that worsen your mood — alcohol, news, isolating environments.",
                "🤝 Tell someone you trust exactly how you're feeling — don't carry this alone.",
            ],
            "SEVERE": [
                "🚨 Please reach out to a mental health professional immediately.",
                "📞 iCall India Helpline: 9152987821 | Vandrevala Foundation: 1860-2662-345 (24/7)",
                "🏥 Consider speaking to a psychiatrist about a structured treatment plan.",
                "🤝 Do not be alone — reach out to family, a close friend, or a professional today.",
            ],
        },

        # ── GAD-7 Anxiety ─────────────────────────────────────
        "GAD7": {
            "MINIMAL": [
                "🧘 Practice box breathing daily: inhale 4s → hold 4s → exhale 4s → hold 4s. Repeat 5x.",
                "☕ Limit caffeine after noon — caffeine directly amplifies anxiety symptoms.",
                "📖 Read for 20 minutes before bed instead of screens to calm the nervous system.",
                "🗓️ Use a simple daily planner to reduce the mental load of 'what-ifs'.",
            ],
            "MILD": [
                "📝 Try worry journaling: write your anxious thought, then write the realistic version of it.",
                "🎵 Use calming music or binaural beats during work or study (search 'anxiety relief binaural beats').",
                "🧘 Practice progressive muscle relaxation before sleep — tense and release each muscle group.",
                "🏃 Exercise daily — physical movement burns off excess adrenaline that fuels anxiety.",
                "📵 Set a 'no news after 8pm' rule — nighttime anxiety is often worsened by media.",
            ],
            "MODERATE": [
                "🧠 Explore CBT-based anxiety apps: Woebot, Sanvello, or Wysa.",
                "🌬️ Practice 4-7-8 breathing: inhale 4s, hold 7s, exhale 8s — activates parasympathetic system.",
                "📋 Write a 'worry time' — schedule 15 minutes/day to only worry then. Rest of the time, defer it.",
                "🏊 Try swimming or yoga — both are clinically shown to reduce GAD symptoms.",
                "👥 Consider group therapy for anxiety — shared experiences reduce the shame around it.",
                "🩺 Visit a doctor to rule out physical causes (thyroid, etc.) that mimic anxiety.",
            ],
            "SEVERE": [
                "🏥 Please consult a psychiatrist or clinical psychologist for a proper anxiety treatment plan.",
                "📞 iCall India: 9152987821 | NIMHANS Helpline: 080-46110007",
                "💊 Medication combined with therapy has strong evidence for severe GAD — speak to a doctor.",
                "🤝 Tell someone close to you what you're experiencing — secrecy amplifies anxiety.",
            ],
        },

        # ── Rosenberg Self-Esteem ─────────────────────────────
        "ROSENBERG": {
            "HIGH SELF-ESTEEM": [
                "✅ Your self-esteem is strong — keep nurturing it!",
                "🎯 Set a new personal challenge or goal to keep growing.",
                "🤝 Mentor or support someone else — teaching builds self-worth further.",
                "📔 Keep a 'wins journal' — record small daily accomplishments.",
            ],
            "NORMAL SELF-ESTEEM": [
                "📔 Write 3 things you did well each evening — build the habit of self-acknowledgment.",
                "🎯 Set one small, achievable goal per week and celebrate completing it.",
                "🤝 Spend more time with people who genuinely encourage and respect you.",
                "📚 Read: 'The Six Pillars of Self-Esteem' by Nathaniel Branden.",
            ],
            "LOW SELF-ESTEEM": [
                "🧠 Start CBT journaling: identify negative self-talk → challenge it → write a balanced truth.",
                "🪞 Practice daily affirmations — not generic ones, but specific to your strengths.",
                "🚫 Set boundaries with people or environments that consistently make you feel small.",
                "🏆 Make a list of 10 things you've accomplished in your life — revisit it when you feel low.",
                "👥 Consider seeing a therapist focused on self-esteem and inner critic work.",
            ],
            "VERY LOW SELF-ESTEEM": [
                "🏥 Please speak to a therapist — very low self-esteem often underlies depression and anxiety.",
                "📞 iCall India: 9152987821",
                "🤝 Confide in one trusted person about how you're feeling about yourself.",
                "🚫 Avoid social comparison, especially on Instagram/social media — it directly worsens self-esteem.",
                "📔 Journal daily: 'What is one thing I did okay today?' Start tiny.",
            ],
        },

        # ── Big Five Personality ──────────────────────────────
        "BIGFIVE": {
            "HIGH TRAIT EXPRESSION": [
                "🎯 Your personality traits are strongly expressed — use them intentionally.",
                "🤝 High extraversion? Channel it into leadership or community building.",
                "📚 High openness? Explore a new creative or intellectual domain this month.",
                "⚖️ High conscientiousness? Perfect for project-based goals — set a 30-day challenge.",
            ],
            "MODERATE TRAIT EXPRESSION": [
                "🔍 Explore your Big Five profile in more depth at personalitytest.net — it's free.",
                "📔 Journal about a situation where your personality helped you — and one where it held you back.",
                "🌱 Work on one trait deliberately: if you want more openness, try one new experience per week.",
            ],
            "LOW TRAIT EXPRESSION": [
                "🌱 Low scores on Big Five traits aren't bad — they may mean you're adaptable and context-sensitive.",
                "📚 Read: 'Quiet' by Susan Cain (if low extraversion) — reframe introversion as a strength.",
                "🎯 Identify which trait you'd like to develop and set one small weekly practice around it.",
            ],
        },
    }

    # Fetch the right recommendations
    cat_recs = recs.get(cat, {})
    level_recs = cat_recs.get(lvl, [
        "🌿 Practice daily mindfulness for 10 minutes.",
        "🏃 Exercise regularly — 30 minutes a day.",
        "😴 Prioritize 7–8 hours of quality sleep.",
        "🤝 Stay socially connected with people you trust.",
        "🩺 Consider speaking to a mental health professional if symptoms persist.",
    ])

    return level_recs


# =============================================================
# CHECK IF USER HAS TAKEN ASSESSMENT
# =============================================================
df_check = pd.read_sql(
    "SELECT COUNT(*) FROM responses WHERE user_id = %s",
    conn, params=(user_id,)
)
response_count = df_check.iloc[0, 0]

# -------------------------------------------------------------
# NEW USER
# -------------------------------------------------------------
if response_count == 0:
    st.subheader(f"Welcome, {username} 👋")
    st.info("You haven't taken the assessment yet. Let's get started!")
    if st.button("📝 Start Assessment"):
        st.switch_page("pages/3_Questionnaire.py")
    st.stop()

# -------------------------------------------------------------
# RETURNING USER
# -------------------------------------------------------------
st.subheader(f"Welcome back, {username} 👋")

# ── Load Scores ──────────────────────────────────────────────
df_scores = pd.read_sql("""
    SELECT c.category_name, s.score_value
    FROM scores s
    JOIN categories c ON s.category_id = c.category_id
    WHERE s.user_id = %s
""", conn, params=(user_id,))

if df_scores.empty:
    st.warning("No scores found. Please take the assessment.")
    st.stop()

# ── Add Interpretation Columns ───────────────────────────────
df_scores["Level"]  = df_scores.apply(
    lambda x: interpret_score(x["category_name"], x["score_value"])[0], axis=1
)
df_scores["Status"] = df_scores.apply(
    lambda x: interpret_score(x["category_name"], x["score_value"])[1], axis=1
)

# =============================================================
# SECTION 1 — SCORE TABLE
# =============================================================
st.subheader("📊 Your Mental Health Scores")
st.dataframe(df_scores, use_container_width=True)

# =============================================================
# SECTION 2 — BAR CHART (fixed for zero scores)
# =============================================================
st.subheader("📈 Score Overview")

fig, ax = plt.subplots(figsize=(10, 4))

colors = [
    interpret_score(row["category_name"], row["score_value"])[2]
    for _, row in df_scores.iterrows()
]

# ── KEY FIX: use a minimum display height of 0.4 for zero scores ──
display_values = [max(v, 0.4) for v in df_scores["score_value"]]

bars = ax.bar(
    df_scores["category_name"],
    display_values,           # ← visual height (never truly 0)
    color=colors,
    edgecolor="white",
    linewidth=0.8,
    width=0.5
)

# Label each bar with the REAL score value (not the padded display value)
for bar, real_val in zip(bars, df_scores["score_value"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.2,
        str(real_val),        # ← always shows true score
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold"
    )

max_val = df_scores["score_value"].max()
ax.set_ylim(0, max(max_val + 3, 6))
ax.set_ylabel("Score", fontsize=11)
ax.set_xlabel("Category", fontsize=11)
ax.set_title("Mental Health Category Scores", fontsize=13, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)

st.pyplot(fig)

# =============================================================
# SECTION 3 — TRENDS OVER TIME
# =============================================================
df_trend = pd.read_sql("""
    SELECT c.category_name, s.score_value, s.created_at
    FROM scores s
    JOIN categories c ON s.category_id = c.category_id
    WHERE s.user_id = %s
    ORDER BY s.created_at
""", conn, params=(user_id,))

if not df_trend.empty and df_trend["created_at"].nunique() > 1:
    st.subheader("📉 Mental Health Trends Over Time")
    df_trend["created_at"] = pd.to_datetime(df_trend["created_at"])
    pivot_df = df_trend.pivot(
        index="created_at",
        columns="category_name",
        values="score_value"
    )
    st.line_chart(pivot_df)
else:
    st.info("📉 Trends will appear after you complete more than one assessment over time.")

# =============================================================
# SECTION 4 — RECOMMENDATIONS (specific & actionable)
# =============================================================
st.subheader("💡 Personalized Recommendations")
st.markdown("Based on your scores, here are specific activities tailored for you:")

for _, row in df_scores.iterrows():

    category = row["category_name"]
    score    = row["score_value"]
    level, emoji, _ = interpret_score(category, score)

    with st.expander(f"{emoji} {category} — {level} (Score: {score})", expanded=True):

        recommendations = get_recommendations(category, level)

        for rec in recommendations:
            st.markdown(f"- {rec}")

# =============================================================
# ACTIONS
# =============================================================
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Retake Assessment"):
        st.switch_page("pages/3_Questionnaire.py")

with col2:
    if st.button("👤 View Profile"):
        st.switch_page("pages/4_Research_Info.py")

conn.close()

st.markdown("---")
st.caption("Built with ❤️ by Aakash Kushwah")