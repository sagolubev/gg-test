import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")
SECRET_KEY = "super-secret-key-12345"
DEBUG = True
UPLOAD_DIR = "uploads"
ADMIN_PASSWORD = "admin123"
