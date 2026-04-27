# NoteKeeper API

Simple REST API for personal notes. FastAPI + SQLite.

## Quick Start

```bash
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

API: http://localhost:8000
Docs: http://localhost:8000/docs

## Configuration

`ALLOWED_ORIGINS` is a comma-separated list of browser origins allowed for credentialed CORS requests.
