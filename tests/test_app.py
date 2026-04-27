from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import app as app_module

app_module.init_db()
client = TestClient(app_module.app)


def _register_and_login():
    username = f"user_{uuid4().hex}"
    password = f"pw_{uuid4().hex}"
    resp = client.post("/register", json={"username": username, "password": password})
    assert resp.status_code == 200
    resp = client.post("/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return {"x-token": resp.json()["token"]}


def test_register():
    resp = client.post(
        "/register",
        json={"username": f"testuser_{uuid4().hex}", "password": "pass123"},
    )
    assert resp.status_code == 200


def test_login():
    username = f"loginuser_{uuid4().hex}"
    client.post("/register", json={"username": username, "password": "pass123"})
    resp = client.post("/login", json={"username": username, "password": "pass123"})
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_create_note():
    headers = _register_and_login()
    resp = client.post(
        "/notes",
        json={"title": "Test", "content": "Body"},
        headers=headers,
    )
    assert resp.status_code == 200


def test_calc():
    resp = client.post("/calc", json={"expression": "2 + 2"})
    assert resp.json()["result"] == 4


def test_upload_allows_image_under_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(tmp_path))
    headers = _register_and_login()

    resp = client.post(
        "/upload",
        files={"file": ("avatar.png", b"fake png", "image/png")},
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "avatar.png"
    saved_path = Path(data["path"]).resolve()
    assert saved_path == (tmp_path / "avatar.png").resolve()
    assert saved_path.read_bytes() == b"fake png"


def test_upload_sanitizes_traversal_filename(tmp_path, monkeypatch):
    upload_dir = tmp_path / "safe" / "uploads"
    outside_path = tmp_path / "etc" / "cron.d" / "evil.png"
    outside_path.parent.mkdir(parents=True)
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(upload_dir))
    headers = _register_and_login()

    resp = client.post(
        "/upload",
        files={"file": ("../../etc/cron.d/evil.png", b"fake png", "image/png")},
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "evil.png"
    assert ".." not in data["path"]
    assert (upload_dir / "evil.png").read_bytes() == b"fake png"
    assert not outside_path.exists()


def test_upload_rejects_unsupported_file_type(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(tmp_path))
    headers = _register_and_login()

    resp = client.post(
        "/upload",
        files={"file": ("avatar.txt", b"text", "text/plain")},
        headers=headers,
    )

    assert resp.status_code == 415
    assert not (tmp_path / "avatar.txt").exists()


def test_upload_rejects_oversized_file(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(app_module, "UPLOAD_MAX_BYTES", 3)
    headers = _register_and_login()

    resp = client.post(
        "/upload",
        files={"file": ("avatar.png", b"too large", "image/png")},
        headers=headers,
    )

    assert resp.status_code == 413
    assert not (tmp_path / "avatar.png").exists()


@pytest.mark.parametrize("headers", [{}, {"x-token": "invalid"}])
def test_upload_requires_valid_token(tmp_path, monkeypatch, headers):
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(tmp_path))

    resp = client.post(
        "/upload",
        files={"file": ("avatar.png", b"fake png", "image/png")},
        headers=headers,
    )

    assert resp.status_code == 401
    assert not (tmp_path / "avatar.png").exists()
