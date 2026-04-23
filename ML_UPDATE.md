# ML Learning Update

## Current ML Status

- Model type: `RandomForestClassifier`
- Training script: `scripts/train_model.py`
- Saved model path: `models/risk_model.pkl`
- Inference API: `POST /predict` in `api/main.py`

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

## Data Dependencies

The model training depends on:

- `assessment_attempts` table
- `scores` table with `attempt_id`
- `categories` table for category mapping

If these are missing, training will fail.

## How to Train

Run from project root:

```bash
python scripts/train_model.py
```

Expected output includes:

- Model save confirmation
- Accuracy score (printed to terminal)

## How to Verify Inference

1. Start API:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

2. Open docs:

- `http://localhost:8000/docs`

3. Test `POST /predict` with sample payload:

```json
{
  "phq9": 12,
  "gad7": 8,
  "rosenberg": 15,
  "bigfive": 18,
  "mood": "Stressed",
  "attempts": 2,
  "trend": 3
}
```

Expected response:

- `risk_probability` (float)
- `risk_level` (`Low` / `Moderate` / `High`)

## Next Improvements

- Add cross-validation and confusion matrix reporting
- Save feature importances after training
- Add model version metadata (timestamp, training rows, schema hash)
- Add fallback behavior in API when model file is missing
