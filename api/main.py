from pathlib import Path

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Mental Health Risk API")

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "risk_model.pkl"
MOOD_ENCODING = {
    "Calm": 0,
    "Neutral": 1,
    "Stressed": 2,
    "Anxious": 3,
    "Low": 4,
}

model = joblib.load(MODEL_PATH)


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


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    mood_value = MOOD_ENCODING.get(payload.mood)
    if mood_value is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported mood. Use one of: {', '.join(MOOD_ENCODING.keys())}",
        )

    features = np.array(
        [[
            payload.phq9,
            payload.gad7,
            payload.rosenberg,
            payload.bigfive,
            mood_value,
            payload.attempts,
            payload.trend,
        ]],
        dtype=float,
    )

    risk_probability = float(model.predict_proba(features)[0][1])

    if risk_probability < 0.4:
        risk_level = "Low"
    elif risk_probability <= 0.7:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    return PredictResponse(
        risk_probability=risk_probability,
        risk_level=risk_level,
    )
