# Mental Wellness Analytics System

Production-oriented Streamlit + FastAPI + PostgreSQL mental wellness platform with reverse-scored assessments, PyTorch risk prediction, synthetic-data training, Docker/Kubernetes deployment assets, and generated HTML code-book documentation.

## Core capabilities
- Reverse-scored assessment engine for `PHQ9`, `GAD7`, `Rosenberg`, and `BigFive`.
- Attempt-aware response and score persistence in PostgreSQL / Supabase.
- Streamlit dashboard with score interpretation, trends, and personalized recommendations.
- FastAPI inference service that serves a PyTorch binary risk model.
- Synthetic-data training path for CI, local development, and environments without production score rows.
- GitHub Actions for tests, training validation, and image builds.
- Kubernetes manifests for Streamlit, API, and DB migration jobs.

## Architecture
```text
Streamlit UI -> PostgreSQL / Supabase <- Questionnaire / Profile / Dashboard
        |
        +-> FastAPI /predict -> PyTorch model artifacts
```

## Project structure
```text
app.py
api/
auth/
database/
docs/
k8s/
pages/
scripts/
src/
tests/
ui/
```

### `src/` layers
- `src/config`: typed settings and environment resolution.
- `src/db`: shared database connection code.
- `src/services`: scoring and authentication logic.
- `src/ml`: feature shaping, torch model, and training pipeline.
- `src/api`: FastAPI app implementation.

## Reverse scoring
Reverse-scored questions are loaded from `questions.is_reversed` and scored through the shared scoring service in `src/services/scoring.py`.

Forward-scored question:
- `raw_value = 3` -> `score = 3`

Reverse-scored question:
- `raw_value = 3` -> `score = 0`
- `raw_value = 0` -> `score = 3`

Automated tests live in `tests/test_scoring.py`.

## Database
- Development bootstrap SQL: `01_database_setup.sql`
- Production migration: `database/migrations/001_initial_schema.sql`

The production migration removes destructive reset behavior and keeps the schema idempotent.

## Environment and secrets
- Local Streamlit secrets: `.streamlit/secrets.toml`
- Example env file: `.env.example`
- Git ignores `.streamlit/secrets.toml`

Required values:
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`

Optional values:
- `MENTAL_HEALTH_API_KEY`
- `USE_SYNTHETIC_TRAINING_DATA`
- `SYNTHETIC_TRAINING_DATA_PATH`
- `MODEL_DIR`

## Local run
Install dependencies:

```bash
pip install -r requirements.txt
```

Run Streamlit:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Run API:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Train the PyTorch model
Generate synthetic data:

```bash
python scripts/generate_synthetic_training_data.py --rows 10000 --users 1200
```

Train from synthetic data only:

```bash
python scripts/train_model.py --synthetic-only --auto-generate-synthetic
```

Artifacts:
- `models/risk_model.pt`
- `models/model_metadata.json`
- `models/training_metrics.json`
- `ML_UPDATE.md`

## Docker
Run both services:

```bash
docker compose up --build
```

The compose file expects DB credentials and optional API key via environment variables.

## Kubernetes
Kubernetes assets are in `k8s/`:
- namespace
- configmap
- secret template
- streamlit deployment/service
- api deployment/service
- migration job

Apply example sequence:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.example.yaml
kubectl apply -f k8s/db-schema-configmap.yaml
kubectl apply -f k8s/db-migration-job.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/streamlit-deployment.yaml
kubectl apply -f k8s/streamlit-service.yaml
```

## CI/CD
GitHub workflows live in `.github/workflows/`:
- `ci.yml`: tests, synthetic generation, torch training, and image builds
- `container-publish.yml`: pushes container images to GHCR

## HTML code book
Generate the line-by-line HTML documentation:

```bash
python scripts/generate_book_docs.py
```

Output:
- `docs/book/index.html`
