from src.db.connection import get_connection as _get_connection
from src.db.connection import get_connection_or_none


def get_connection():
    return get_connection_or_none()


__all__ = ["get_connection", "get_connection_or_none", "_get_connection"]
