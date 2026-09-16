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


def _redis_url() -> str:
    # Même logique que _database_url() : REDIS_HOST=localhost hors Docker,
    # REDIS_HOST=redis (nom du service) dans docker-compose.
    host = os.environ.get("REDIS_HOST", "localhost")
    port = os.environ.get("REDIS_PORT", "6379")
    return f"redis://{host}:{port}/0"


DATABASE_URL = _database_url()
REDIS_URL = _redis_url()

# --- Paiement Mobile Money ---
PAYMENT_PROVIDER = os.environ.get("PAYMENT_PROVIDER", "simulator")
CINETPAY_API_KEY = os.environ.get("CINETPAY_API_KEY", "")
CINETPAY_SITE_ID = os.environ.get("CINETPAY_SITE_ID", "")
CINETPAY_SECRET_KEY = os.environ.get("CINETPAY_SECRET_KEY", "")
CINETPAY_NOTIFY_URL = os.environ.get("CINETPAY_NOTIFY_URL", "")
CINETPAY_BASE_URL = os.environ.get("CINETPAY_BASE_URL", "https://api-checkout.cinetpay.com")
# Secret utilisé par le provider `simulator` pour auto-signer ses webhooks de
# test (HMAC) — jamais utilisé en production, aucun rapport avec CinetPay.
SIMULATOR_SECRET = os.environ.get("SIMULATOR_SECRET", "dev-simulator-secret")
