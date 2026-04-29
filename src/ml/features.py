from __future__ import annotations

from pathlib import Path

import pandas as pd


MOOD_ENCODING = {
    "Calm": 0,
    "Neutral": 1,
    "Stressed": 2,
    "Anxious": 3,
    "Low": 4,
}

FEATURE_COLUMNS = ["phq9", "gad7", "rosenberg", "bigfive", "mood", "attempts", "trend"]


def synthetic_path_from_string(path_value: str) -> Path:
    return Path(path_value)


def load_external_synthetic_feature_rows(synthetic_path: Path) -> pd.DataFrame:
    if not synthetic_path.exists():
        raise FileNotFoundError(f"Synthetic training data file not found: {synthetic_path}")

    synthetic_df = pd.read_csv(synthetic_path)
    required_columns = {
        "user_id",
        "attempt_id",
        "attempt_number",
        "created_at",
        "mood_label",
        "phq9",
        "gad7",
        "rosenberg",
        "bigfive",
    }
    missing_columns = required_columns - set(synthetic_df.columns)
    if missing_columns:
        raise RuntimeError(
            "Synthetic training data is missing required columns: " + ", ".join(sorted(missing_columns))
        )

    synthetic_df["created_at"] = pd.to_datetime(synthetic_df["created_at"], utc=True, errors="coerce")
    if synthetic_df["created_at"].isna().any():
        raise RuntimeError("Synthetic training data contains invalid created_at values.")

    if "trend" not in synthetic_df.columns:
        synthetic_df["trend"] = 0.0

    return synthetic_df[
        [
            "user_id",
            "attempt_id",
            "attempt_number",
            "created_at",
            "mood_label",
            "phq9",
            "gad7",
            "rosenberg",
            "bigfive",
            "trend",
        ]
    ].copy()


def build_feature_frame(feature_df: pd.DataFrame) -> pd.DataFrame:
    shaped = feature_df.copy()
    shaped["created_at"] = pd.to_datetime(shaped["created_at"], utc=True, errors="coerce")
    if shaped["created_at"].isna().any():
        raise RuntimeError("Training data contains invalid created_at values.")

    for required_col in ["phq9", "gad7", "rosenberg", "bigfive"]:
        if required_col not in shaped.columns:
            shaped[required_col] = 0

    shaped["mood"] = shaped["mood_label"].map(MOOD_ENCODING).fillna(1).astype(int)
    shaped["attempts"] = shaped["attempt_number"].fillna(1).astype(float)
    shaped = shaped.sort_values(["user_id", "created_at", "attempt_id"])
    shaped["total_score"] = shaped["phq9"] + shaped["gad7"] + shaped["rosenberg"] + shaped["bigfive"]

    if "trend" not in shaped.columns:
        shaped["trend"] = shaped.groupby("user_id")["total_score"].diff().fillna(0.0)
    else:
        shaped["trend"] = pd.to_numeric(shaped["trend"], errors="coerce").fillna(0.0)

    shaped["risk_label"] = (shaped["phq9"] >= 10).astype(int)
    return shaped
