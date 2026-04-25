from fastapi.testclient import TestClient

from app import app

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
