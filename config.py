import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")
SECRET_KEY = "super-secret-key-12345"
DEBUG = True
UPLOAD_DIR = "uploads"
ADMIN_PASSWORD = "admin123"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://localhost:3000",
    ).split(",")
    if origin.strip()
]
