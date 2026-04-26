import atexit
import os
from pathlib import Path

from fastapi.testclient import TestClient

TEST_DB = Path(".test-notes.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
atexit.register(lambda: TEST_DB.exists() and TEST_DB.unlink())

from app import app
from database import init_db

init_db()
client = TestClient(app)


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


def test_frontend_note_rendering_avoids_html_injection():
    js = Path("static/js/app.js").read_text()

    assert "eval(" not in js
    assert "renderTemplate" not in js
    assert "${note.title}" not in js
    assert "${note.content}" not in js
    assert 'value="${note.title}"' not in js
    assert "title.textContent = note.title" in js
    assert "content.textContent = note.content" in js
    assert "titleInput.value = note.title" in js
    assert "contentTextarea.value = note.content" in js
