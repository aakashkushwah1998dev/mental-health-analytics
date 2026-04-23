from pathlib import Path
import sys
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.connection import get_connection  # noqa: E402


MOOD_ENCODING = {
    "Calm": 0,
    "Neutral": 1,
    "Stressed": 2,
    "Anxious": 3,
    "Low": 4,
}


def write_ml_update(accuracy: float, training_rows: int, model_path: Path) -> None:
    update_path = Path(__file__).resolve().parents[1] / "ML_UPDATE.md"
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    content = f"""# ML Learning Update

## Auto-Updated Training Snapshot

- Last trained at: `{updated_at}`
- Model type: `RandomForestClassifier`
- Training script: `scripts/train_model.py`
- Saved model path: `{model_path}`
- Training rows: `{training_rows}`
- Accuracy: `{accuracy:.4f}`

## Features Used by Model

- `phq9`
- `gad7`
- `rosenberg`
- `bigfive`
- `mood` (encoded: Calm=0, Neutral=1, Stressed=2, Anxious=3, Low=4)
- `attempts`
- `trend` (current total score - previous total score)

## Label Definition

- `risk_label = 1` if `phq9 >= 10`
- `risk_label = 0` otherwise

## Inference Endpoint

- `POST /predict` in `api/main.py`
- Output: `risk_probability`, `risk_level`
"""
    update_path.write_text(content, encoding="utf-8")


def main() -> None:
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Database connection failed.")

    df = pd.read_sql(
        """
        SELECT
            s.user_id,
            s.attempt_id,
            a.attempt_number,
            a.created_at,
            a.mood_label,
            c.category_name,
            s.score_value
        FROM scores s
        JOIN assessment_attempts a ON s.attempt_id = a.attempt_id
        JOIN categories c ON s.category_id = c.category_id
        WHERE s.attempt_id IS NOT NULL
        ORDER BY s.user_id, a.created_at, s.attempt_id
        """,
        conn,
    )
    conn.close()

    if df.empty:
        raise RuntimeError("No score data found for training.")

    feature_df = (
        df.pivot_table(
            index=["user_id", "attempt_id", "attempt_number", "created_at", "mood_label"],
            columns="category_name",
            values="score_value",
            aggfunc="first",
        )
        .reset_index()
        .fillna(0)
    )

    feature_df.columns = [str(col).lower() for col in feature_df.columns]

    for required_col in ["phq9", "gad7", "rosenberg", "bigfive"]:
        if required_col not in feature_df.columns:
            feature_df[required_col] = 0

    feature_df["mood"] = feature_df["mood_label"].map(MOOD_ENCODING).fillna(1).astype(int)
    feature_df["attempts"] = feature_df["attempt_number"].fillna(1).astype(float)

    feature_df = feature_df.sort_values(["user_id", "created_at", "attempt_id"])
    feature_df["total_score"] = (
        feature_df["phq9"] + feature_df["gad7"] + feature_df["rosenberg"] + feature_df["bigfive"]
    )
    feature_df["trend"] = feature_df.groupby("user_id")["total_score"].diff().fillna(0.0)

    feature_df["risk_label"] = (feature_df["phq9"] >= 10).astype(int)

    X = feature_df[["phq9", "gad7", "rosenberg", "bigfive", "mood", "attempts", "trend"]]
    y = feature_df["risk_label"]

    if y.nunique() < 2:
        raise RuntimeError("Need both risk classes to train a classifier.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    model_dir = Path(__file__).resolve().parents[1] / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "risk_model.pkl"
    joblib.dump(model, model_path)
    write_ml_update(accuracy=accuracy, training_rows=len(feature_df), model_path=model_path)

    print(f"Model saved to: {model_path}")
    print(f"Accuracy: {accuracy:.4f}")
    print("ML update report refreshed: ML_UPDATE.md")


if __name__ == "__main__":
    main()
