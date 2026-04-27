from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

from app import app
from config import ALLOWED_ORIGINS

client = TestClient(app)


def test_cors_middleware_uses_configured_origins_without_wildcard_credentials():
    middleware = next(item for item in app.user_middleware if item.cls is CORSMiddleware)
    options = getattr(middleware, "kwargs", getattr(middleware, "options", {}))

    assert options["allow_credentials"] is True
    assert options["allow_origins"] == ALLOWED_ORIGINS
    assert options["allow_origins"] != ["*"]


def test_cors_preflight_allows_configured_origin():
    origin = ALLOWED_ORIGINS[0]
    resp = client.options(
        "/notes",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == origin
    assert resp.headers["access-control-allow-credentials"] == "true"


def test_cors_preflight_rejects_unconfigured_origin():
    resp = client.options(
        "/notes",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert resp.status_code == 400
    assert "access-control-allow-origin" not in resp.headers


def test_register():
    resp = client.post("/register", json={"username": "testuser", "password": "pass123"})
    assert resp.status_code == 200


def test_login():
    client.post("/register", json={"username": "loginuser", "password": "pass123"})
    resp = client.post("/login", json={"username": "loginuser", "password": "pass123"})
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_create_note():
    client.post("/register", json={"username": "noteuser", "password": "pw"})
    resp = client.post("/login", json={"username": "noteuser", "password": "pw"})
    token = resp.json()["token"]
    resp = client.post("/notes", json={"title": "Test", "content": "Body"}, headers={"x-token": token})
    assert resp.status_code == 200


def test_calc():
    resp = client.post("/calc", json={"expression": "2 + 2"})
    assert resp.json()["result"] == 4
