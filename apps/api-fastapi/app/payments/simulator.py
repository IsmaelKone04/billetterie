"""Provider de paiement `simulator` — permet de dérouler tout le flux
achat → paiement → émission de billets sans identifiants CinetPay réels
(aucun organisateur réel à ce stade). Le webhook est auto-signé (HMAC) par
ce même service : il n'y a pas de système externe distinct à interroger,
donc pas d'appel « check » séparé (`requires_check = False`)."""

import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from decimal import Decimal
from typing import Literal

from ..config import SIMULATOR_SECRET
from .base import PaymentCheckResult, PaymentInitiation, PaymentProvider, WebhookEvent


def sign(timestamp: str, body: str) -> str:
    message = f"{timestamp}.{body}".encode()
    return hmac.new(SIMULATOR_SECRET.encode(), message, hashlib.sha256).hexdigest()


def build_signed_webhook(
    *, transaction_id: str, event_id: str, outcome: Literal["success", "failed"]
) -> tuple[dict[str, str], bytes]:
    """Construit un webhook de test signé — utilisé par le endpoint de
    déclenchement dev (`POST /payments/simulate`) et par les tests."""
    status = "ACCEPTED" if outcome == "success" else "REFUSED"
    body = json.dumps(
        {"transaction_id": transaction_id, "event_id": event_id, "status": status}
    )
    timestamp = str(int(time.time()))
    # En minuscules : les en-têtes HTTP réels arrivent normalisés en
    # minuscules côté ASGI (`dict(request.headers)`) — même convention ici
    # pour que /payments/simulate (appel direct, sans passer par le réseau)
    # produise exactement ce que parse_webhook() reçoit en production.
    headers = {
        "x-simulator-timestamp": timestamp,
        "x-simulator-signature": sign(timestamp, body),
    }
    return headers, body.encode()


class SimulatorProvider(PaymentProvider):
    name = "simulator"
    requires_check = False

    async def initiate(
        self,
        *,
        transaction_id: str,
        amount: Decimal,
        buyer_phone: str,
        buyer_email: str,
        description: str,
    ) -> PaymentInitiation:
        # Pas de redirection externe en mode simulateur : le paiement est
        # déclenché manuellement via POST /payments/simulate (dev/tests).
        return PaymentInitiation(payment_url=None)

    def parse_webhook(self, headers: Mapping[str, str], raw_body: bytes) -> WebhookEvent:
        timestamp = headers.get("x-simulator-timestamp", "")
        signature = headers.get("x-simulator-signature", "")
        body_str = raw_body.decode()
        expected = sign(timestamp, body_str)
        signature_valid = hmac.compare_digest(signature, expected)

        payload = json.loads(body_str)
        status = payload.get("status")
        event_type = "payment.accepted" if status == "ACCEPTED" else "payment.refused"

        return WebhookEvent(
            provider_event_id=str(payload.get("event_id")),
            transaction_id=str(payload.get("transaction_id")),
            event_type=event_type,
            signature_valid=signature_valid,
            raw_payload=payload,
        )

    async def check(self, transaction_id: str) -> PaymentCheckResult:
        # Jamais appelé (requires_check = False) : le webhook auto-signé est
        # la seule source de vérité du simulateur.
        raise NotImplementedError(
            "SimulatorProvider.check() ne devrait jamais être appelé "
            "(requires_check = False)"
        )
