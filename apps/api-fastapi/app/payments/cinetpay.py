"""Provider de paiement **CinetPay** (agrégateur Mobile Money dominant en
Côte d'Ivoire : Orange Money, MTN MoMo, Moov Money, Wave via un seul
contrat). Parcours : `initiate` → POST /v2/payment (URL de paiement hébergée
à rediriger) ; webhook `notify_url` (form-urlencoded, en-tête `x-token` =
HMAC-SHA256 de la concaténation ordonnée de 16 champs `cpm_*`) ; puis POST
/v2/payment/check pour le statut faisant foi — jamais de confiance aveugle
au webhook seul (recommandation officielle CinetPay).

Ordre des champs et logique repris tels quels de l'intégration monbail
(apps/api/src/payments/providers/cinetpay.provider.ts), déjà éprouvée en
conditions réelles sur ce marché."""

import hashlib
import hmac
import math
from collections.abc import Mapping
from decimal import Decimal
from urllib.parse import parse_qsl

import httpx

from ..config import (
    CINETPAY_API_KEY,
    CINETPAY_BASE_URL,
    CINETPAY_NOTIFY_URL,
    CINETPAY_SECRET_KEY,
    CINETPAY_SITE_ID,
)
from .base import PaymentCheckResult, PaymentInitiation, PaymentProvider, WebhookEvent

_SIGNATURE_FIELDS = [
    "cpm_site_id",
    "cpm_trans_id",
    "cpm_trans_date",
    "cpm_amount",
    "cpm_currency",
    "signature",
    "payment_method",
    "cel_phone_num",
    "cpm_phone_prefixe",
    "cpm_language",
    "cpm_version",
    "cpm_payment_config",
    "cpm_page_action",
    "cpm_custom",
    "cpm_designation",
    "cpm_error_message",
]


class CinetPayProvider(PaymentProvider):
    name = "cinetpay"
    requires_check = True

    def _require_credentials(self) -> None:
        if not (CINETPAY_API_KEY and CINETPAY_SITE_ID and CINETPAY_SECRET_KEY):
            raise RuntimeError(
                "PAYMENT_PROVIDER=cinetpay mais CINETPAY_API_KEY / CINETPAY_SITE_ID / "
                "CINETPAY_SECRET_KEY ne sont pas renseignés (identifiants réels non "
                "disponibles à ce stade — voir docs/RAPPORT.md)."
            )

    async def initiate(
        self,
        *,
        transaction_id: str,
        amount: Decimal,
        buyer_phone: str,
        buyer_email: str,
        description: str,
    ) -> PaymentInitiation:
        self._require_credentials()
        # CinetPay exige des montants XOF multiples de 5 : arrondi au
        # multiple supérieur (écart de quelques FCFA accepté).
        rounded_amount = int(math.ceil(float(amount) / 5) * 5)
        body = {
            "apikey": CINETPAY_API_KEY,
            "site_id": CINETPAY_SITE_ID,
            "transaction_id": transaction_id,
            "amount": rounded_amount,
            "currency": "XOF",
            "description": description,
            "channels": "MOBILE_MONEY",
            "lang": "fr",
            "notify_url": CINETPAY_NOTIFY_URL,
            "customer_phone_number": buyer_phone,
            "metadata": buyer_email,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{CINETPAY_BASE_URL}/v2/payment", json=body)
        data = response.json()
        if str(data.get("code")) != "201" or not data.get("data", {}).get("payment_url"):
            raise RuntimeError(
                f"Initiation CinetPay refusée : {data.get('code')} {data.get('message', '')}"
            )
        return PaymentInitiation(payment_url=str(data["data"]["payment_url"]))

    def parse_webhook(self, headers: Mapping[str, str], raw_body: bytes) -> WebhookEvent:
        form = dict(parse_qsl(raw_body.decode()))
        message = "".join(form.get(field, "") for field in _SIGNATURE_FIELDS)
        expected = hmac.new(
            CINETPAY_SECRET_KEY.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        provided = headers.get("x-token", "").strip()
        signature_valid = bool(provided) and hmac.compare_digest(expected, provided)

        return WebhookEvent(
            # Provisoire : le webhook seul ne fait pas foi, seul /check
            # détermine le statut définitif (voir handler d'appel dans
            # routers/payments.py, qui recalcule le provider_event_id final
            # après check() pour la déduplication).
            provider_event_id=f"cinetpay:{form.get('cpm_trans_id', '')}:webhook",
            transaction_id=form.get("cpm_trans_id", ""),
            event_type="notification",
            signature_valid=signature_valid,
            raw_payload=form,
        )

    async def check(self, transaction_id: str) -> PaymentCheckResult:
        self._require_credentials()
        body = {
            "apikey": CINETPAY_API_KEY,
            "site_id": CINETPAY_SITE_ID,
            "transaction_id": transaction_id,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{CINETPAY_BASE_URL}/v2/payment/check", json=body)
        data = response.json()
        status = str(data.get("data", {}).get("status", "")).upper()
        code = str(data.get("code"))
        if status == "ACCEPTED" and code == "00":
            return PaymentCheckResult(status="success")
        if status == "REFUSED" or code == "627":
            return PaymentCheckResult(status="failed")
        return PaymentCheckResult(status="pending")
