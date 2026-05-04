# =============================================================
# DASHBOARD PAGE
# Author: Aakash Kushwah
# =============================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from pathlib import Path
from urllib import error, request
import torch
from database.connection import get_connection
from src.config.settings import load_settings
from src.ml.features import FEATURE_COLUMNS, MOOD_ENCODING
from src.ml.model import RiskPredictionModel
from ui.session_controls import render_logout_button

# -------------------------------------------------------------
# SESSION CHECK
# -------------------------------------------------------------
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Please login first.")
    st.stop()

user_id  = st.session_state.get("user_id")
username = st.session_state.get("username")

st.title("📊 Mental Wellness Dashboard")
render_logout_button()
st.info(
    "These scores support self-awareness only.\n"
    "This is not a medical diagnosis."
)

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
def get_recommendations(category: str, level: str, mood: str | None = None) -> list:
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

    if cat == "PHQ9" and lvl in {"MODERATE", "MODERATELY SEVERE", "SEVERE"} and (mood or "").strip().lower() == "stressed":
        level_recs = ["Try box breathing: 4 seconds in, hold 4, out 4"] + level_recs

    return level_recs


def get_score_value(df_scores: pd.DataFrame, category_name: str) -> float:
    match = df_scores.loc[df_scores["category_name"].str.upper() == category_name.upper(), "score_value"]
    if match.empty:
        return 0.0
    return float(match.iloc[0])


def resolve_local_model_path(settings) -> Path | None:
    project_root = Path(__file__).resolve().parents[1]
    candidates = []
    if settings.model_path:
        candidates.append(Path(settings.model_path))
    if settings.model_dir:
        candidates.append(Path(settings.model_dir) / "risk_model.pt")
    candidates.append(project_root / "models" / "risk_model.pt")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_local_metadata_path(settings) -> Path | None:
    project_root = Path(__file__).resolve().parents[1]
    candidates = []
    if settings.model_path:
        candidates.append(Path(settings.model_path).with_name("model_metadata.json"))
    if settings.model_dir:
        candidates.append(Path(settings.model_dir) / "model_metadata.json")
    candidates.append(project_root / "models" / "model_metadata.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


@st.cache_resource(show_spinner=False)
def load_local_risk_model(model_path: str):
    checkpoint = torch.load(model_path, map_location="cpu")
    input_dim = int(checkpoint["input_dim"])
    local_model = RiskPredictionModel(input_dim=input_dim)
    local_model.load_state_dict(checkpoint["model_state_dict"])
    local_model.eval()
    return local_model


def fetch_local_ai_risk_prediction(payload: dict) -> tuple[dict | None, str | None]:
    settings = load_settings()
    mood_value = MOOD_ENCODING.get(str(payload["mood"]))
    if mood_value is None:
        return None, "Unsupported mood for local prediction fallback."

    model_path = resolve_local_model_path(settings)
    metadata_path = resolve_local_metadata_path(settings)
    if model_path is None:
        return None, "Local model file is missing."

    feature_columns = FEATURE_COLUMNS
    if metadata_path and metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            feature_columns = metadata.get("feature_columns") or FEATURE_COLUMNS
        except Exception:
            feature_columns = FEATURE_COLUMNS

    feature_map = {
        "phq9": float(payload["phq9"]),
        "gad7": float(payload["gad7"]),
        "rosenberg": float(payload["rosenberg"]),
        "bigfive": float(payload["bigfive"]),
        "mood": float(mood_value),
        "attempts": float(payload["attempts"]),
        "trend": float(payload["trend"]),
    }
    features = pd.DataFrame([[feature_map[column] for column in feature_columns]], columns=feature_columns)
    feature_tensor = torch.tensor(features.values, dtype=torch.float32)

    local_model = load_local_risk_model(str(model_path))
    with torch.no_grad():
        logits = local_model(feature_tensor)
        risk_probability = float(torch.sigmoid(logits).item())

    if risk_probability < 0.4:
        risk_level = "Low"
    elif risk_probability <= 0.7:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    return {
        "risk_probability": risk_probability,
        "risk_level": risk_level,
        "_source": "Local model fallback",
    }, None


def fetch_local_model_info() -> tuple[dict | None, str | None]:
    settings = load_settings()
    metadata_path = resolve_local_metadata_path(settings)
    if metadata_path is None:
        return None, "Local model metadata file is missing."

    try:
        model_info = json.loads(metadata_path.read_text(encoding="utf-8"))
        model_info["_source"] = "Local metadata fallback"
        return model_info, None
    except Exception as exc:
        return None, f"Unable to read local model metadata: {exc}"


def fetch_ai_risk_prediction(
    df_scores: pd.DataFrame,
    latest_mood: str | None,
    attempts: int,
    trend_value: float,
) -> tuple[dict | None, str | None]:
    settings = load_settings()
    api_url = settings.mental_health_api_url
    payload = {
        "phq9": get_score_value(df_scores, "PHQ9"),
        "gad7": get_score_value(df_scores, "GAD7"),
        "rosenberg": get_score_value(df_scores, "Rosenberg"),
        "bigfive": get_score_value(df_scores, "BigFive"),
        "mood": latest_mood or "Neutral",
        "attempts": float(attempts),
        "trend": float(trend_value),
    }

    headers = {"Content-Type": "application/json"}
    if settings.api_security.api_key:
        headers["x-api-key"] = settings.api_security.api_key

    http_request = request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=5) as response:
            body = response.read().decode("utf-8")
            response_payload = json.loads(body)
            response_payload["_source"] = "FastAPI service"
            return response_payload, None
    except error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = exc.reason
        local_prediction, local_error = fetch_local_ai_risk_prediction(payload)
        if local_prediction:
            local_prediction["_source_detail"] = (
                f"FastAPI returned {exc.code}; the dashboard used the saved local model instead."
            )
            return local_prediction, None
        return None, f"API returned {exc.code}: {error_body}"
    except Exception as exc:
        local_prediction, local_error = fetch_local_ai_risk_prediction(payload)
        if local_prediction:
            local_prediction["_source_detail"] = (
                f"FastAPI is unreachable ({exc}); the dashboard used the saved local model instead."
            )
            return local_prediction, None
        return None, local_error or str(exc)


def fetch_model_info() -> tuple[dict | None, str | None]:
    settings = load_settings()
    headers = {}
    if settings.api_security.api_key:
        headers["x-api-key"] = settings.api_security.api_key
    http_request = request.Request(settings.mental_health_model_info_url, headers=headers, method="GET")

    try:
        with request.urlopen(http_request, timeout=5) as response:
            body = response.read().decode("utf-8")
            model_info = json.loads(body)
            model_info["_source"] = "FastAPI service"
            return model_info, None
    except error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = exc.reason
        local_model_info, local_error = fetch_local_model_info()
        if local_model_info:
            local_model_info["_source_detail"] = (
                f"FastAPI model info returned {exc.code}; the dashboard used saved local metadata instead."
            )
            return local_model_info, None
        return None, f"Model info API returned {exc.code}: {error_body}"
    except Exception as exc:
        local_model_info, local_error = fetch_local_model_info()
        if local_model_info:
            local_model_info["_source_detail"] = (
                f"FastAPI model info is unreachable ({exc}); the dashboard used saved local metadata instead."
            )
            return local_model_info, None
        return None, local_error or str(exc)


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
        st.switch_page("pages/4_Questionnaire.py")
    st.stop()

# -------------------------------------------------------------
# RETURNING USER
# -------------------------------------------------------------
st.subheader(f"Welcome back, {username} 👋")

# ── Load Assessment Attempts ─────────────────────────────────
df_attempts = pd.read_sql("""
    SELECT attempt_id, created_at, mood_label
    FROM assessment_attempts
    WHERE user_id = %s
    ORDER BY created_at
""", conn, params=(user_id,))

latest_mood = None
latest_attempt_display = "N/A"
total_assessments = 0

if not df_attempts.empty:
    df_attempts["created_at"] = pd.to_datetime(df_attempts["created_at"])
    latest_attempt = df_attempts.iloc[-1]
    latest_attempt_id = int(latest_attempt["attempt_id"])
    latest_mood = latest_attempt["mood_label"]
    latest_attempt_display = latest_attempt["created_at"].strftime("%Y-%m-%d %H:%M")
    total_assessments = int(len(df_attempts))

    # ── Load Latest Attempt Scores (default view) ────────────────
    df_scores = pd.read_sql("""
        SELECT c.category_name, s.score_value
        FROM scores s
        JOIN categories c ON s.category_id = c.category_id
        WHERE s.user_id = %s AND s.attempt_id = %s
    """, conn, params=(user_id, latest_attempt_id))
else:
    # Legacy fallback for rows created before attempt tracking
    df_scores = pd.read_sql("""
        WITH latest_score_time AS (
            SELECT MAX(created_at) AS max_created_at
            FROM scores
            WHERE user_id = %s
        )
        SELECT c.category_name, s.score_value
        FROM scores s
        JOIN categories c ON s.category_id = c.category_id
        JOIN latest_score_time lst ON s.created_at = lst.max_created_at
        WHERE s.user_id = %s
    """, conn, params=(user_id, user_id))
    latest_attempt_display = "Legacy score snapshot"
    total_assessments = int(pd.read_sql(
        "SELECT COUNT(DISTINCT created_at) AS attempts FROM scores WHERE user_id = %s",
        conn,
        params=(user_id,)
    ).iloc[0]["attempts"])

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

# ── Summary Card Data ────────────────────────────────────────
severity_rank = {
    "MINIMAL": 1,
    "MILD": 2,
    "NORMAL SELF-ESTEEM": 2,
    "MODERATE": 3,
    "LOW SELF-ESTEEM": 3,
    "MODERATELY SEVERE": 4,
    "VERY LOW SELF-ESTEEM": 4,
    "SEVERE": 5,
}

levels_for_latest = [
    interpret_score(row["category_name"], row["score_value"])[0]
    for _, row in df_scores.iterrows()
]
overall_risk = max(
    levels_for_latest,
    key=lambda x: severity_rank.get(x.upper(), 0)
) if levels_for_latest else "N/A"

if not df_attempts.empty:
    df_attempt_totals = pd.read_sql("""
        SELECT a.attempt_id, a.created_at, COALESCE(SUM(s.score_value), 0) AS total_score
        FROM assessment_attempts a
        LEFT JOIN scores s ON s.attempt_id = a.attempt_id
        WHERE a.user_id = %s
        GROUP BY a.attempt_id, a.created_at
        ORDER BY a.created_at
    """, conn, params=(user_id,))
else:
    df_attempt_totals = pd.read_sql("""
        SELECT created_at, SUM(score_value) AS total_score
        FROM scores
        WHERE user_id = %s
        GROUP BY created_at
        ORDER BY created_at
    """, conn, params=(user_id,))

trend_label = "Stable"
trend_value = 0.0
if len(df_attempt_totals) >= 2:
    previous_total = df_attempt_totals.iloc[-2]["total_score"]
    latest_total = df_attempt_totals.iloc[-1]["total_score"]
    trend_value = float(latest_total - previous_total)
    if latest_total < previous_total:
        trend_label = "Improving"
    elif latest_total > previous_total:
        trend_label = "Declining"
    else:
        trend_label = "Stable"

ai_prediction, ai_prediction_error = fetch_ai_risk_prediction(
    df_scores=df_scores,
    latest_mood=latest_mood,
    attempts=total_assessments,
    trend_value=trend_value,
)
model_info, model_info_error = fetch_model_info()

# =============================================================
# SUMMARY CARD
# =============================================================
st.subheader("🧾 Assessment Summary")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Last Assessment", latest_attempt_display)
with col2:
    st.metric("Total Assessments", total_assessments)
with col3:
    st.metric("Overall Risk Level", overall_risk)
with col4:
    st.metric("Trend", trend_label)

# =============================================================
# AI RISK PREDICTION
# =============================================================
st.subheader("🤖 AI Risk Prediction")

if ai_prediction:
    prediction_probability = float(ai_prediction["risk_probability"]) * 100
    prediction_level = ai_prediction["risk_level"]

    pred_col1, pred_col2, pred_col3 = st.columns(3)
    with pred_col1:
        st.metric("Predicted Risk", prediction_level)
    with pred_col2:
        st.metric("Risk Probability", f"{prediction_probability:.1f}%")
    with pred_col3:
        st.metric("Mood Used", latest_mood or "Neutral")

    st.caption(
        ai_prediction.get("_source_detail")
        or "This prediction comes from the configured ML model using your latest "
        "assessment scores, mood, attempt count, and score trend."
    )
else:
    st.warning("AI prediction is currently unavailable.")
    if ai_prediction_error:
        st.caption(ai_prediction_error)

# =============================================================
# ML MODEL STATUS
# =============================================================
st.subheader("🧪 ML Model Status")

if model_info:
    real_training_rows = int(model_info.get("real_training_rows") or 0)
    total_training_rows = int(model_info.get("training_rows") or 0)
    synthetic_training_rows = int(model_info.get("synthetic_training_rows") or 0)
    used_synthetic_bootstrap = bool(model_info.get("used_synthetic_bootstrap"))

    if used_synthetic_bootstrap or synthetic_training_rows > 0 or real_training_rows < 10:
        model_quality_label = "Dev-quality"
        model_quality_help = (
            "This model is usable for local testing, but the training dataset is still too "
            "small for production confidence."
        )
    else:
        model_quality_label = "Real-data"
        model_quality_help = (
            "This model was trained on real assessment rows without synthetic bootstrap data."
        )

    model_col1, model_col2, model_col3, model_col4 = st.columns(4)
    with model_col1:
        st.metric("Model Type", model_info.get("model_type") or "Unknown")
    with model_col2:
        st.metric("Model Quality", model_quality_label)
    with model_col3:
        st.metric("Real Training Rows", real_training_rows)
    with model_col4:
        st.metric("Synthetic Rows", synthetic_training_rows)

    st.caption(model_quality_help)
    if model_info.get("_source_detail"):
        st.caption(model_info["_source_detail"])

    with st.expander("View model metadata"):
        st.write(f"**Metadata Source:** {model_info.get('_source') or 'Unknown'}")
        st.write(f"**Trained At:** {model_info.get('trained_at_utc') or 'Unknown'}")
        st.write(f"**Schema Hash:** {model_info.get('schema_hash') or 'Unknown'}")
        st.write(f"**Total Training Rows:** {total_training_rows}")
        st.write(
            f"**Synthetic Bootstrap Used:** {'Yes' if used_synthetic_bootstrap else 'No'}"
        )
        feature_columns = model_info.get("feature_columns") or []
        if feature_columns:
            st.write("**Features Used:** " + ", ".join(feature_columns))
else:
    st.warning("Model metadata is currently unavailable.")
    if model_info_error:
        st.caption(model_info_error)

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
show_history = st.toggle("View Full History")

df_trend = pd.read_sql("""
    SELECT c.category_name, s.score_value, s.created_at, s.attempt_id
    FROM scores s
    JOIN categories c ON s.category_id = c.category_id
    WHERE s.user_id = %s
    ORDER BY s.created_at, s.attempt_id
""", conn, params=(user_id,))

if show_history and not df_trend.empty and df_trend["created_at"].nunique() > 1:
    st.subheader("📉 Mental Health Trends Over Time")
    df_trend["created_at"] = pd.to_datetime(df_trend["created_at"])
    df_trend["attempt_label"] = df_trend["created_at"].dt.strftime("%Y-%m-%d %H:%M")
    if df_trend["attempt_id"].notna().any():
        df_trend["attempt_label"] = (
            df_trend["attempt_label"]
            + " (#" + df_trend["attempt_id"].fillna(0).astype(int).astype(str) + ")"
        )
    pivot_df = df_trend.pivot(
        index="attempt_label",
        columns="category_name",
        values="score_value"
    )
    st.line_chart(pivot_df)
elif show_history:
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

        recommendations = get_recommendations(category, level, latest_mood)

        for rec in recommendations:
            st.markdown(f"- {rec}")

# =============================================================
# ACTIONS
# =============================================================
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Retake Assessment"):
        st.switch_page("pages/4_Questionnaire.py")

with col2:
    if st.button("👤 View Profile"):
        st.switch_page("pages/2_Research_Info.py")

conn.close()

st.markdown("---")
st.caption("Built with ❤️ by Aakash Kushwah")
