"""Authentification organisateur : hachage de mot de passe (PBKDF2-HMAC-
SHA256, stdlib uniquement, pas de dépendance supplémentaire) et session sous
forme de JWT signé avec ORGANIZER_JWT_SECRET. Distinct du token QR des
billets (app/services/qr.py) : deux usages de signature différents, deux
secrets différents."""

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from ..config import ORGANIZER_JWT_SECRET

PBKDF2_ITERATIONS = 200_000
TOKEN_TTL = timedelta(hours=12)


class AuthConfigError(Exception):
    """ORGANIZER_JWT_SECRET n'est pas configuré."""


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations_str, salt_hex, hash_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations_str)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def create_organizer_token(organizer_id: int) -> str:
    if not ORGANIZER_JWT_SECRET:
        raise AuthConfigError("ORGANIZER_JWT_SECRET n'est pas configuré")
    now = datetime.now(timezone.utc)
    payload = {"sub": str(organizer_id), "iat": now, "exp": now + TOKEN_TTL}
    return jwt.encode(payload, ORGANIZER_JWT_SECRET, algorithm="HS256")


def decode_organizer_token(token: str) -> int | None:
    if not ORGANIZER_JWT_SECRET:
        return None
    try:
        payload = jwt.decode(token, ORGANIZER_JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
