"""Token QR d'un billet : un HMAC-SHA256 de (ticket_id, qr_secret) signé
avec JWT_SECRET — jamais le qr_secret en clair. Même si le token fuite, il
ne révèle pas qr_secret ; et sans JWT_SECRET, impossible d'en fabriquer un
nouveau pour un autre ticket_id. Génération et vérification recalculent
toujours le HMAC (rien n'est stocké en base au-delà de qr_secret)."""

import base64
import hashlib
import hmac

from ..config import JWT_SECRET


class QrConfigError(Exception):
    """JWT_SECRET n'est pas configuré — impossible de signer/vérifier un QR."""


def _sign(ticket_id: int, qr_secret: str) -> str:
    if not JWT_SECRET:
        raise QrConfigError("JWT_SECRET n'est pas configuré")
    digest = hmac.new(
        JWT_SECRET.encode(), f"{ticket_id}:{qr_secret}".encode(), hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def build_qr_token(ticket_id: int, qr_secret: str) -> str:
    return f"{ticket_id}.{_sign(ticket_id, qr_secret)}"


def parse_ticket_id(token: str) -> int | None:
    """Extrait le ticket_id sans vérifier la signature — la vérification se
    fait ensuite avec verify_qr_token(), une fois le qr_secret réel relu en
    base pour ce ticket_id."""
    ticket_id_str, sep, signature = token.partition(".")
    if not sep or not ticket_id_str.isdigit() or not signature:
        return None
    return int(ticket_id_str)


def verify_qr_token(token: str, ticket_id: int, qr_secret: str) -> bool:
    try:
        expected = build_qr_token(ticket_id, qr_secret)
    except QrConfigError:
        return False
    return hmac.compare_digest(token, expected)
