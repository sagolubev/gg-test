import hashlib
import hmac
import secrets

from database import get_db


PASSWORD_HASH_PREFIX = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 260_000


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    ).hex()
    return f"{PASSWORD_HASH_PREFIX}${PASSWORD_HASH_ITERATIONS}${salt}${digest}"


def _verify_password(password: str, stored_password: str) -> bool:
    if not stored_password.startswith(f"{PASSWORD_HASH_PREFIX}$"):
        return hmac.compare_digest(password, stored_password)

    try:
        _, iterations, salt, expected_digest = stored_password.split("$", 3)
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(actual_digest, expected_digest)


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def register_user(username: str, password: str, email: str = None):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, _hash_password(password), email),
        )
        conn.commit()
        return {"username": username, "status": "created"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


def login_user(username: str, password: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if not row or not _verify_password(password, row["password"]):
        conn.close()
        return None

    if not row["password"].startswith(f"{PASSWORD_HASH_PREFIX}$"):
        conn.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (_hash_password(password), row["id"]),
        )

    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO auth_tokens (token_hash, user_id) VALUES (?, ?)",
        (_token_digest(token), row["id"]),
    )
    conn.commit()
    conn.close()
    return {"user_id": row["id"], "username": row["username"], "token": token}


def get_user_by_token(token: str):
    conn = get_db()
    row = conn.execute(
        """
        SELECT users.id, users.username
        FROM users
        JOIN auth_tokens ON auth_tokens.user_id = users.id
        WHERE auth_tokens.token_hash = ?
        """,
        (_token_digest(token),),
    ).fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "username": row["username"]}
    return None
