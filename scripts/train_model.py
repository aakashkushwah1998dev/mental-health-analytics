from pathlib import Path
import sys
from datetime import datetime, timezone
import hashlib
import json
import os
import tempfile

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split, cross_val_score

sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.connection import get_connection  # noqa: E402


MOOD_ENCODING = {
    "Calm": 0,
    "Neutral": 1,
    "Stressed": 2,
    "Anxious": 3,
    "Low": 4,
}


def build_schema_hash(feature_columns: list[str]) -> str:
    joined = "|".join(feature_columns)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def resolve_writable_model_dir() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    preferred = Path(os.getenv("MODEL_DIR", str(project_root / "models")))
    fallback = Path(tempfile.gettempdir()) / "mental-health-analytics" / "models"

    for candidate in [preferred, fallback]:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue

    raise RuntimeError("No writable directory available for model artifacts.")


def write_model_metadata(
    model_dir: Path,
    model_path: Path,
    training_rows: int,
    feature_columns: list[str],
    accuracy: float,
    cv_mean: float,
    cv_std: float,
) -> Path:
    metadata_path = model_dir / "model_metadata.json"
    payload = {
        "model_type": "RandomForestClassifier",
        "trained_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "model_path": str(model_path),
        "training_rows": int(training_rows),
        "feature_columns": feature_columns,
        "schema_hash": build_schema_hash(feature_columns),
        "accuracy": round(float(accuracy), 4),
        "cv_mean_accuracy": round(float(cv_mean), 4),
        "cv_std_accuracy": round(float(cv_std), 4),
    }
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return metadata_path


def write_ml_update(
    accuracy: float,
    training_rows: int,
    model_path: Path,
    cv_mean: float,
    cv_std: float,
    cm: list[list[int]],
    schema_hash: str,
) -> None:
    configured_update_path = os.getenv("ML_UPDATE_PATH")
    if configured_update_path:
        update_path = Path(configured_update_path)
    else:
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
- Cross-validation (5-fold) mean accuracy: `{cv_mean:.4f}`
- Cross-validation (5-fold) std: `{cv_std:.4f}`
- Schema hash: `{schema_hash}`

## Confusion Matrix (Test Set)

```text
{cm[0][0]}  {cm[0][1]}
{cm[1][0]}  {cm[1][1]}
```

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
    try:
        update_path.write_text(content, encoding="utf-8")
    except Exception:
        fallback_update_path = resolve_writable_model_dir().parent / "ML_UPDATE.md"
        fallback_update_path.write_text(content, encoding="utf-8")


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
    feature_columns = list(X.columns)

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
    cm = confusion_matrix(y_test, predictions, labels=[0, 1]).tolist()
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    cv_mean = float(cv_scores.mean())
    cv_std = float(cv_scores.std())

    model_dir = resolve_writable_model_dir()
    model_path = model_dir / "risk_model.pkl"
    joblib.dump(model, model_path)

    importance_path = model_dir / "feature_importances.csv"
    pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False).to_csv(importance_path, index=False)

    metadata_path = write_model_metadata(
        model_dir=model_dir,
        model_path=model_path,
        training_rows=len(feature_df),
        feature_columns=feature_columns,
        accuracy=accuracy,
        cv_mean=cv_mean,
        cv_std=cv_std,
    )

    schema_hash = build_schema_hash(feature_columns)
    write_ml_update(
        accuracy=accuracy,
        training_rows=len(feature_df),
        model_path=model_path,
        cv_mean=cv_mean,
        cv_std=cv_std,
        cm=cm,
        schema_hash=schema_hash,
    )

    print(f"Model saved to: {model_path}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Cross-val mean accuracy (5-fold): {cv_mean:.4f}")
    print(f"Cross-val std accuracy (5-fold): {cv_std:.4f}")
    print(f"Confusion matrix (test): {cm}")
    print(f"Feature importances saved to: {importance_path}")
    print(f"Model metadata saved to: {metadata_path}")
    print("ML update report refreshed: ML_UPDATE.md")


if __name__ == "__main__":
    main()
