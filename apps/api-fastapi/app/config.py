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


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


DATABASE_URL = _database_url()
REDIS_URL = _redis_url()
# Origines autorisées à appeler cette API depuis un navigateur (apps/web en
# dev par défaut). Pas un secret — juste la liste des frontends de confiance,
# à ajuster en production via CORS_ALLOWED_ORIGINS (séparées par des virgules).
CORS_ALLOWED_ORIGINS = _cors_origins()

# Même logique que DJANGO_DEBUG côté admin-django : autorise un secret de
# dev par défaut uniquement quand API_DEBUG=true, sinon un secret manquant
# reste vide (les endpoints qui en dépendent refusent alors explicitement,
# plutôt que de tourner avec un secret devinable en production).
API_DEBUG = os.environ.get("API_DEBUG", "false").lower() == "true"


def _secret(name: str, dev_fallback: str) -> str:
    value = os.environ.get(name, "")
    if value:
        return value
    return dev_fallback if API_DEBUG else ""


# Signe/vérifie le token QR des billets (voir app/services/qr.py).
JWT_SECRET = _secret("JWT_SECRET", "insecure-dev-only-jwt-secret-do-not-use-in-production")
# Clé partagée exigée dans l'en-tête X-Scan-Key de POST /scan — protège
# l'endpoint qui invalide les billets. Pas de compte staff dédié pour
# l'instant (voir docs/RAPPORT.md, ouvert au jalon M4).
SCAN_API_KEY = _secret("SCAN_API_KEY", "insecure-dev-only-scan-key-do-not-use-in-production")
# Signe le JWT de session organisateur (voir app/services/auth.py) — secret
# distinct de JWT_SECRET pour ne jamais partager la même clé entre deux
# usages de signature différents (token QR billet vs session organisateur).
ORGANIZER_JWT_SECRET = _secret(
    "ORGANIZER_JWT_SECRET", "insecure-dev-only-organizer-jwt-secret-do-not-use-in-production"
)

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
