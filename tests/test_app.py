import atexit
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_db_fd, _db_path = tempfile.mkstemp(prefix="notekeeper-test-", suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
atexit.register(lambda: os.path.exists(_db_path) and os.unlink(_db_path))

from app import app
from database import init_db

init_db()
client = TestClient(app)
APP_JS = Path(__file__).resolve().parents[1] / "static" / "js" / "app.js"


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


def test_login_return_url_validation_removes_direct_redirect():
    app_js = APP_JS.read_text()

    assert "window.location.href = returnUrl" not in app_js
    assert "function getSafeReturnUrl" in app_js
    assert "new URL(rawReturnUrl, window.location.origin)" in app_js
    assert 'rawReturnUrl.startsWith("//")' in app_js
    assert 'rawReturnUrl.includes("\\\\")' in app_js
    assert "url.origin !== window.location.origin" in app_js


def test_login_return_url_validation_cases():
    if not shutil.which("node"):
        pytest.skip("node is required for frontend helper regression coverage")

    app_js = APP_JS.read_text()
    script = f"""
const vm = require("vm");
const source = {json.dumps(app_js)};
const context = {{
  window: {{ location: {{ origin: "https://app.example", search: "" }} }},
  localStorage: {{ getItem() {{}}, setItem() {{}}, removeItem() {{}} }},
  document: {{ getElementById() {{ return {{ innerHTML: "", textContent: "" }}; }} }},
  console,
  URL,
  URLSearchParams
}};
vm.createContext(context);
vm.runInContext(source, context);

const cases = [
  ["https://evil.com/steal", null],
  ["//evil.com/steal", null],
  ["javascript:alert(1)", null],
  ["/\\\\evil.com/steal", null],
  ["/", "/"],
  ["/?search=abc", "/?search=abc"],
  ["/notes#top", "/notes#top"]
];

for (const [input, expected] of cases) {{
  const actual = context.getSafeReturnUrl(input);
  if (actual !== expected) {{
    throw new Error(`${{input}} returned ${{actual}}, expected ${{expected}}`);
  }}
}}
"""
    subprocess.run(["node", "-e", script], check=True)
