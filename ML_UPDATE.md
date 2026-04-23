# ML Learning Update

`ML_UPDATE.md` is automatically rewritten by `scripts/train_model.py` on each training run.

## What Gets Auto-Updated

- Training timestamp (UTC)
- Model path
- Training row count
- Accuracy (test split)
- Cross-validation mean/std (5-fold)
- Confusion matrix (test split)
- Feature schema hash

## Additional Generated Artifacts

- `models/feature_importances.csv`
- `models/model_metadata.json`

## Train Command

```bash
python scripts/train_model.py
```

## API Behavior if Model Missing

`api/main.py` returns HTTP 503 with a clear error if `models/risk_model.pkl` is not present.
