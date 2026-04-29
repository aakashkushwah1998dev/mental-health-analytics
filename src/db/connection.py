from __future__ import annotations

import logging

import psycopg2

from src.config.settings import load_settings


logger = logging.getLogger(__name__)


def get_connection():
    settings = load_settings()
    db = settings.database
    return psycopg2.connect(
        host=db.host,
        database=db.name,
        user=db.user,
        password=db.password,
        port=db.port,
    )


def get_connection_or_none():
    try:
        return get_connection()
    except Exception:
        logger.exception("Database connection failed.")
        return None
