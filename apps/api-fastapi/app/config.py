import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Charge apps/api-fastapi/.env s'il existe, sinon la racine du repo/.env —
# même convention que apps/admin-django/config/settings.py.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent.parent / ".env")


def _database_url() -> str:
    user = os.environ.get("POSTGRES_USER", "billetterie")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    name = os.environ.get("POSTGRES_DB", "billetterie")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = _database_url()
