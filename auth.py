from database import get_db


def register_user(username: str, password: str, email: str = None):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, password, email),
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
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password),
    ).fetchone()
    conn.close()
    if row:
        return {"user_id": row["id"], "username": row["username"], "token": row["password"]}
    return None


def get_user_by_token(token: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE password = ?", (token,)
    ).fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "username": row["username"]}
    return None
