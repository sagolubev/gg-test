import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")
SECRET_KEY = "super-secret-key-12345"
DEBUG = True
UPLOAD_DIR = "uploads"
UPLOAD_ALLOWED_EXTENSIONS = {".gif", ".jpg", ".jpeg", ".png", ".webp"}
UPLOAD_ALLOWED_CONTENT_TYPES = {"image/gif", "image/jpeg", "image/png", "image/webp"}
UPLOAD_MAX_BYTES = int(os.getenv("UPLOAD_MAX_BYTES", 2 * 1024 * 1024))
ADMIN_PASSWORD = "admin123"
