from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

from src.config.settings import load_settings
from src.db.connection import get_connection_or_none
from src.ml.features import FEATURE_COLUMNS, build_feature_frame, load_external_synthetic_feature_rows
from src.ml.model import RiskPredictionModel


@dataclass(frozen=True)
class TrainingArtifacts:
    model_path: Path
    metadata_path: Path
    metrics_path: Path
    feature_columns: list[str]
    accuracy: float
    training_rows: int
    real_training_rows: int
    synthetic_training_rows: int
    confusion_matrix_values: list[list[int]]


def build_schema_hash(feature_columns: list[str]) -> str:
    joined = "|".join(feature_columns)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def resolve_writable_model_dir() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    settings = load_settings()
    preferred = Path(settings.model_dir)
    if not preferred.is_absolute():
        preferred = project_root / preferred
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


def fetch_database_feature_rows() -> pd.DataFrame:
    conn = get_connection_or_none()
    if conn is None:
        return pd.DataFrame()

    try:
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
    finally:
        conn.close()

    if df.empty:
        return pd.DataFrame()

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
    return feature_df


def build_training_frame(*, synthetic_only: bool = False, auto_generate_synthetic: bool = False) -> tuple[pd.DataFrame, int, int]:
    settings = load_settings()
    project_root = Path(__file__).resolve().parents[2]
    synthetic_path = Path(settings.synthetic_training_data_path)
    if not synthetic_path.is_absolute():
        synthetic_path = project_root / synthetic_path

    if auto_generate_synthetic and not synthetic_path.exists():
        from scripts.generate_synthetic_training_data import build_synthetic_rows

        synthetic_path.parent.mkdir(parents=True, exist_ok=True)
        build_synthetic_rows(row_count=10000, user_count=1200, seed=42).to_csv(synthetic_path, index=False)

    real_df = pd.DataFrame() if synthetic_only else fetch_database_feature_rows()
    real_training_rows = len(real_df)

    synthetic_df = pd.DataFrame()
    if settings.use_synthetic_training_data or synthetic_only or synthetic_path.exists():
        synthetic_df = load_external_synthetic_feature_rows(synthetic_path)

    synthetic_training_rows = len(synthetic_df)
    combined = pd.concat([real_df, synthetic_df], ignore_index=True, sort=False)
    if combined.empty:
        raise RuntimeError("No training rows found in database or synthetic dataset.")

    return build_feature_frame(combined), real_training_rows, synthetic_training_rows


def train_torch_model(*, synthetic_only: bool = False, auto_generate_synthetic: bool = False) -> TrainingArtifacts:
    feature_df, real_training_rows, synthetic_training_rows = build_training_frame(
        synthetic_only=synthetic_only,
        auto_generate_synthetic=auto_generate_synthetic,
    )

    X = feature_df[FEATURE_COLUMNS].astype(np.float32)
    y = feature_df["risk_label"].astype(np.float32)
    feature_columns = list(X.columns)

    test_rows = max(2, math.ceil(len(X) * 0.2))
    remaining_train_rows = len(X) - test_rows
    label_counts = y.value_counts()
    can_make_stratified_split = (
        len(X) >= 4
        and y.nunique() >= 2
        and int(label_counts.min()) >= 2
        and test_rows >= y.nunique()
        and remaining_train_rows >= y.nunique()
    )

    if can_make_stratified_split:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_rows,
            random_state=42,
            stratify=y,
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    X_train_tensor = torch.tensor(X_train.values, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train.values, dtype=torch.float32)
    X_test_tensor = torch.tensor(X_test.values, dtype=torch.float32)

    dataset = TensorDataset(X_train_tensor, y_train_tensor)
    dataloader = DataLoader(dataset, batch_size=min(64, len(dataset)), shuffle=True)

    model = RiskPredictionModel(input_dim=len(feature_columns))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCEWithLogitsLoss()

    model.train()
    for _ in range(60):
        for batch_features, batch_labels in dataloader:
            optimizer.zero_grad()
            logits = model(batch_features)
            loss = criterion(logits, batch_labels)
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        logits = model(X_test_tensor)
        probabilities = torch.sigmoid(logits).cpu().numpy()

    predictions = (probabilities >= 0.5).astype(int)
    accuracy = accuracy_score(y_test.astype(int), predictions)
    cm = confusion_matrix(y_test.astype(int), predictions, labels=[0, 1]).tolist()

    model_dir = resolve_writable_model_dir()
    model_path = model_dir / "risk_model.pt"
    metadata_path = model_dir / "model_metadata.json"
    metrics_path = model_dir / "training_metrics.json"

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "input_dim": len(feature_columns),
            "feature_columns": feature_columns,
        },
        model_path,
    )

    metadata = {
        "model_type": "PyTorchBinaryClassifier",
        "trained_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "model_path": str(model_path),
        "training_rows": int(len(feature_df)),
        "real_training_rows": int(real_training_rows),
        "synthetic_training_rows": int(synthetic_training_rows),
        "feature_columns": feature_columns,
        "schema_hash": build_schema_hash(feature_columns),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    metrics_payload = {
        "accuracy": round(float(accuracy), 4),
        "confusion_matrix": cm,
    }
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    return TrainingArtifacts(
        model_path=model_path,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        feature_columns=feature_columns,
        accuracy=float(accuracy),
        training_rows=len(feature_df),
        real_training_rows=real_training_rows,
        synthetic_training_rows=synthetic_training_rows,
        confusion_matrix_values=cm,
    )


def write_ml_update(artifacts: TrainingArtifacts) -> Path:
    settings = load_settings()
    project_root = Path(__file__).resolve().parents[2]
    update_path = Path(settings.ml_update_path)
    if not update_path.is_absolute():
        update_path = project_root / update_path

    content = f"""# ML Learning Update

## Auto-Updated Training Snapshot

- Model type: `PyTorchBinaryClassifier`
- Saved model path: `{artifacts.model_path}`
- Training rows: `{artifacts.training_rows}`
- Real database rows: `{artifacts.real_training_rows}`
- External synthetic rows: `{artifacts.synthetic_training_rows}`
- Accuracy: `{artifacts.accuracy:.4f}`
- Schema hash: `{build_schema_hash(artifacts.feature_columns)}`

## Confusion Matrix

```text
{artifacts.confusion_matrix_values[0][0]}  {artifacts.confusion_matrix_values[0][1]}
{artifacts.confusion_matrix_values[1][0]}  {artifacts.confusion_matrix_values[1][1]}
```
"""
    update_path.write_text(content, encoding="utf-8")
    return update_path
