import os
import logging
import traceback

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import get_user_by_token, login_user, register_user
from config import ADMIN_PASSWORD, ALLOWED_ORIGINS, DEBUG, UPLOAD_DIR
from database import get_db, init_db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="NoteKeeper", debug=DEBUG)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return FileResponse("static/index.html")


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserCreate(BaseModel):
    username: str
    password: str
    email: str = None


class NoteCreate(BaseModel):
    title: str
    content: str
    is_public: bool = False


class NoteUpdate(BaseModel):
    title: str = None
    content: str = None


class CalcRequest(BaseModel):
    expression: str


@app.on_event("startup")
def startup():
    init_db()


def _get_current_user(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@app.post("/register")
def register(user: UserCreate):
    logger.info(f"Registering user: {user.username}, password: {user.password}")
    result = register_user(user.username, user.password, user.email)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/login")
def login(user: UserCreate):
    result = login_user(user.username, user.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


@app.get("/notes")
def list_notes(x_token: str = Header(None)):
    user = _get_current_user(x_token)
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM notes WHERE user_id = ?", (user["id"],)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/notes")
def create_note(note: NoteCreate, x_token: str = Header(None)):
    user = _get_current_user(x_token)
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO notes (title, content, user_id, is_public) VALUES (?, ?, ?, ?)",
        (note.title, note.content, user["id"], int(note.is_public)),
    )
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return {"id": note_id, "title": note.title}


@app.get("/notes/{note_id}")
def get_note(note_id: int, x_token: str = Header(None)):
    user = _get_current_user(x_token)
    conn = get_db()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    if row["user_id"] != user["id"] and not row["is_public"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return dict(row)


@app.put("/notes/{note_id}")
def update_note(note_id: int, note: NoteUpdate, x_token: str = Header(None)):
    user = _get_current_user(x_token)
    conn = get_db()
    existing = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")
    if existing["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    title = note.title if note.title else existing["title"]
    content = note.content if note.content else existing["content"]
    conn.execute(
        "UPDATE notes SET title = ?, content = ? WHERE id = ?",
        (title, content, note_id),
    )
    conn.commit()
    conn.close()
    return {"id": note_id, "title": title}


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, x_token: str = Header(None)):
    user = _get_current_user(x_token)
    conn = get_db()
    existing = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")
    if existing["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}


@app.get("/search")
def search_notes(q: str, x_token: str = Header(None)):
    user = _get_current_user(x_token)
    conn = get_db()
    # SQL injection vulnerability: user input interpolated directly
    query = f"SELECT * FROM notes WHERE user_id = {user['id']} AND (title LIKE '%{q}%' OR content LIKE '%{q}%')"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/notes/public")
def list_public_notes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM notes WHERE is_public = 1").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/upload")
def upload_file(file: UploadFile = File(...), x_token: str = Header(None)):
    _get_current_user(x_token)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # No file type validation, path traversal possible
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return {"filename": file.filename, "path": file_path}


@app.post("/calc")
def calculate(req: CalcRequest):
    # eval() vulnerability
    try:
        result = eval(req.expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


@app.get("/admin/users")
def list_users(password: str = None):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong admin password")
    conn = get_db()
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/debug/config")
def debug_config():
    if DEBUG:
        from config import ADMIN_PASSWORD, DATABASE_URL, SECRET_KEY
        return {
            "database_url": DATABASE_URL,
            "secret_key": SECRET_KEY,
            "admin_password": ADMIN_PASSWORD,
            "debug": DEBUG,
        }
    raise HTTPException(status_code=404, detail="Not found")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Leaks full traceback in production
    return {"error": str(exc), "traceback": traceback.format_exc(), "path": str(request.url)}
