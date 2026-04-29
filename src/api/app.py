from __future__ import annotations

from pathlib import Path
import json
import logging
import tempfile

import pandas as pd
import torch
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from src.config.settings import load_settings
from src.ml.features import FEATURE_COLUMNS, MOOD_ENCODING
from src.ml.model import RiskPredictionModel


logger = logging.getLogger(__name__)
app = FastAPI(title="Mental Health Risk API")

PROJECT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "risk_model.pt"
PROJECT_METADATA_PATH = Path(__file__).resolve().parents[2] / "models" / "model_metadata.json"
TMP_MODEL_PATH = Path(tempfile.gettempdir()) / "mental-health-analytics" / "models" / "risk_model.pt"
TMP_METADATA_PATH = Path(tempfile.gettempdir()) / "mental-health-analytics" / "models" / "model_metadata.json"

model = None
model_metadata = None


def resolve_model_path() -> Path | None:
    settings = load_settings()
    candidates = []
    if settings.model_path:
        candidates.append(Path(settings.model_path))
    if settings.model_dir:
        candidates.append(Path(settings.model_dir) / "risk_model.pt")
    candidates.extend([PROJECT_MODEL_PATH, TMP_MODEL_PATH])

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_metadata_path() -> Path | None:
    settings = load_settings()
    candidates = []
    if settings.model_path:
        candidates.append(Path(settings.model_path).with_name("model_metadata.json"))
    if settings.model_dir:
        candidates.append(Path(settings.model_dir) / "model_metadata.json")
    candidates.extend([PROJECT_METADATA_PATH, TMP_METADATA_PATH])

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def require_api_key(x_api_key: str | None) -> None:
    expected_api_key = load_settings().api_security.api_key
    if expected_api_key and x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key.")


def get_model():
    global model
    if model is not None:
        return model

    model_path = resolve_model_path()
    if model_path is None:
        raise HTTPException(status_code=503, detail="Model file is missing. Train the model first.")

    checkpoint = torch.load(model_path, map_location="cpu")
    input_dim = int(checkpoint["input_dim"])
    loaded_model = RiskPredictionModel(input_dim=input_dim)
    loaded_model.load_state_dict(checkpoint["model_state_dict"])
    loaded_model.eval()
    model = loaded_model
    return model


def get_model_metadata() -> dict:
    global model_metadata
    if model_metadata is not None:
        return model_metadata

    metadata_path = resolve_metadata_path()
    if metadata_path is None:
        model_metadata = {}
        return model_metadata

    model_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return model_metadata


class PredictRequest(BaseModel):
    phq9: float
    gad7: float
    rosenberg: float
    bigfive: float
    mood: str
    attempts: float
    trend: float


class PredictResponse(BaseModel):
    risk_probability: float
    risk_level: str


class ModelInfoResponse(BaseModel):
    model_type: str | None = None
    trained_at_utc: str | None = None
    training_rows: int | None = None
    real_training_rows: int | None = None
    synthetic_training_rows: int | None = None
    feature_columns: list[str] = []
    schema_hash: str | None = None


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, x_api_key: str | None = Header(default=None)) -> PredictResponse:
    require_api_key(x_api_key)

    mood_value = MOOD_ENCODING.get(payload.mood)
    if mood_value is None:
        raise HTTPException(status_code=400, detail=f"Unsupported mood. Use one of: {', '.join(MOOD_ENCODING)}")

    loaded_model = get_model()
    metadata = get_model_metadata()
    feature_columns = metadata.get("feature_columns", FEATURE_COLUMNS)
    feature_map = {
        "phq9": float(payload.phq9),
        "gad7": float(payload.gad7),
        "rosenberg": float(payload.rosenberg),
        "bigfive": float(payload.bigfive),
        "mood": float(mood_value),
        "attempts": float(payload.attempts),
        "trend": float(payload.trend),
    }
    features = pd.DataFrame([[feature_map[column] for column in feature_columns]], columns=feature_columns)
    feature_tensor = torch.tensor(features.values, dtype=torch.float32)

    with torch.no_grad():
        logits = loaded_model(feature_tensor)
        risk_probability = float(torch.sigmoid(logits).item())

    if risk_probability < 0.4:
        risk_level = "Low"
    elif risk_probability <= 0.7:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    return PredictResponse(risk_probability=risk_probability, risk_level=risk_level)


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info(x_api_key: str | None = Header(default=None)) -> ModelInfoResponse:
    require_api_key(x_api_key)
    metadata = get_model_metadata()
    return ModelInfoResponse(
        model_type=metadata.get("model_type"),
        trained_at_utc=metadata.get("trained_at_utc"),
        training_rows=metadata.get("training_rows"),
        real_training_rows=metadata.get("real_training_rows"),
        synthetic_training_rows=metadata.get("synthetic_training_rows"),
        feature_columns=metadata.get("feature_columns", []),
        schema_hash=metadata.get("schema_hash"),
    )
