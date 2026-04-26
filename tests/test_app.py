import logging

import pytest
from fastapi.testclient import TestClient

from app import app
import database
from auth import PASSWORD_HASH_PREFIX
from database import get_db, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    init_db()


def test_register():
    resp = client.post("/register", json={"username": "testuser", "password": "pass123"})
    assert resp.status_code == 200

    conn = get_db()
    row = conn.execute(
        "SELECT password FROM users WHERE username = ?", ("testuser",)
    ).fetchone()
    conn.close()
    assert row["password"] != "pass123"
    assert row["password"].startswith(f"{PASSWORD_HASH_PREFIX}$")


def test_login():
    client.post("/register", json={"username": "loginuser", "password": "pass123"})
    resp = client.post("/login", json={"username": "loginuser", "password": "pass123"})
    assert resp.status_code == 200
    assert "token" in resp.json()
    assert resp.json()["token"] != "pass123"

    conn = get_db()
    row = conn.execute(
        "SELECT password FROM users WHERE username = ?", ("loginuser",)
    ).fetchone()
    conn.close()
    assert resp.json()["token"] != row["password"]


def test_login_invalid_credentials_returns_401():
    client.post("/register", json={"username": "invaliduser", "password": "pass123"})
    resp = client.post("/login", json={"username": "invaliduser", "password": "wrong"})
    assert resp.status_code == 401


def test_create_note():
    client.post("/register", json={"username": "noteuser", "password": "pw"})
    resp = client.post("/login", json={"username": "noteuser", "password": "pw"})
    token = resp.json()["token"]
    resp = client.post("/notes", json={"title": "Test", "content": "Body"}, headers={"x-token": token})
    assert resp.status_code == 200

    resp = client.get("/notes", headers={"x-token": token})
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Test"


def test_raw_password_rejected_as_token():
    client.post("/register", json={"username": "rawtokenuser", "password": "pw"})
    resp = client.post("/login", json={"username": "rawtokenuser", "password": "pw"})
    token = resp.json()["token"]

    assert client.get("/notes", headers={"x-token": token}).status_code == 200
    assert client.get("/notes", headers={"x-token": "pw"}).status_code == 401


def test_register_does_not_log_password(caplog):
    caplog.set_level(logging.INFO, logger="app")
    resp = client.post(
        "/register",
        json={"username": "loguser", "password": "do-not-log-this"},
    )

    assert resp.status_code == 200
    assert "loguser" in caplog.text
    assert "do-not-log-this" not in caplog.text


def test_calc():
    resp = client.post("/calc", json={"expression": "2 + 2"})
    assert resp.json()["result"] == 4
