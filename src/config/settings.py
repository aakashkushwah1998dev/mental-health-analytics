from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


def _read_streamlit_secret(key: str) -> str | None:
    try:
        import streamlit as st  # Imported lazily so non-UI code stays decoupled.

        value: Any = st.secrets.get(key)
        return str(value) if value is not None else None
    except Exception:
        return None


def get_setting(key: str, default: str | None = None, *, allow_streamlit_secret: bool = True) -> str | None:
    env_value = os.getenv(key)
    if env_value not in (None, ""):
        return env_value

    if allow_streamlit_secret:
        secret_value = _read_streamlit_secret(key)
        if secret_value not in (None, ""):
            return secret_value

    return default


def get_required_setting(key: str, *, allow_streamlit_secret: bool = True) -> str:
    value = get_setting(key, allow_streamlit_secret=allow_streamlit_secret)
    if value in (None, ""):
        raise ValueError(f"Missing required setting: {key}")
    return value


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    name: str
    user: str
    password: str
    port: int


@dataclass(frozen=True)
class ApiSecuritySettings:
    api_key: str | None


@dataclass(frozen=True)
class AppSettings:
    database: DatabaseSettings
    api_security: ApiSecuritySettings
    model_dir: str
    model_path: str | None
    mental_health_api_url: str
    mental_health_model_info_url: str
    allow_dev_synthetic_data: bool
    use_synthetic_training_data: bool
    synthetic_training_data_path: str
    ml_update_path: str


def load_settings() -> AppSettings:
    return AppSettings(
        database=DatabaseSettings(
            host=get_required_setting("DB_HOST"),
            name=get_required_setting("DB_NAME"),
            user=get_required_setting("DB_USER"),
            password=get_required_setting("DB_PASSWORD"),
            port=int(get_setting("DB_PORT", "5432") or "5432"),
        ),
        api_security=ApiSecuritySettings(
            api_key=get_setting("MENTAL_HEALTH_API_KEY", allow_streamlit_secret=False),
        ),
        model_dir=get_setting("MODEL_DIR", "models", allow_streamlit_secret=False) or "models",
        model_path=get_setting("MODEL_PATH", allow_streamlit_secret=False),
        mental_health_api_url=(
            get_setting("MENTAL_HEALTH_API_URL", "http://127.0.0.1:8000/predict", allow_streamlit_secret=False)
            or "http://127.0.0.1:8000/predict"
        ),
        mental_health_model_info_url=(
            get_setting(
                "MENTAL_HEALTH_MODEL_INFO_URL",
                "http://127.0.0.1:8000/model-info",
                allow_streamlit_secret=False,
            )
            or "http://127.0.0.1:8000/model-info"
        ),
        allow_dev_synthetic_data=(get_setting("ALLOW_DEV_SYNTHETIC_DATA", "", allow_streamlit_secret=False) == "1"),
        use_synthetic_training_data=(
            get_setting("USE_SYNTHETIC_TRAINING_DATA", "", allow_streamlit_secret=False) == "1"
        ),
        synthetic_training_data_path=(
            get_setting(
                "SYNTHETIC_TRAINING_DATA_PATH",
                os.path.join("data", "generated", "synthetic_assessments.csv"),
                allow_streamlit_secret=False,
            )
            or os.path.join("data", "generated", "synthetic_assessments.csv")
        ),
        ml_update_path=(
            get_setting("ML_UPDATE_PATH", "ML_UPDATE.md", allow_streamlit_secret=False) or "ML_UPDATE.md"
        ),
    )
