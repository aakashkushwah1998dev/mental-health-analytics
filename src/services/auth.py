from __future__ import annotations

from dataclasses import dataclass

import bcrypt

from src.db.connection import get_connection


@dataclass(frozen=True)
class AuthResult:
    status: str
    user_id: int | None = None
    username: str | None = None


def login_or_register(username: str, password: str) -> AuthResult:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT user_id, password FROM users WHERE username = %s",
            (username,),
        )
        user = cursor.fetchone()

        if user:
            user_id, stored_password = user
            if bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
                return AuthResult(status="login_success", user_id=user_id, username=username)
            return AuthResult(status="login_failed")

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING user_id",
            (username, hashed_password),
        )
        new_user_id = cursor.fetchone()[0]
        conn.commit()
        return AuthResult(status="register_success", user_id=new_user_id, username=username)
    finally:
        cursor.close()
        conn.close()
