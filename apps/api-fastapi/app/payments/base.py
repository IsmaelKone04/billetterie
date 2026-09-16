"""Interface commune aux providers de paiement Mobile Money — pattern
`PaymentProvider` repris de monbail (providers/payment-provider.ts), qui
permet de basculer entre CinetPay (réel) et `simulator` (dev, sans
identifiants marchands) via la seule variable d'env PAYMENT_PROVIDER."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass
class PaymentInitiation:
    payment_url: str | None


@dataclass
class WebhookEvent:
    provider_event_id: str
    transaction_id: str
    event_type: str
    signature_valid: bool
    raw_payload: dict


@dataclass
class PaymentCheckResult:
    status: Literal["success", "failed", "pending"]


class PaymentProvider(ABC):
    name: str

    # CinetPay impose un appel POST /v2/payment/check avant d'émettre les
    # billets : le webhook seul n'est jamais une preuve suffisante de
    # paiement (recommandation officielle CinetPay, repris de monbail).
    # Le provider `simulator` n'a pas de système externe distinct à
    # interroger : son webhook auto-signé EST la source de vérité, donc pas
    # de second appel « check ».
    requires_check: bool = True

    @abstractmethod
    async def initiate(
        self,
        *,
        transaction_id: str,
        amount: Decimal,
        buyer_phone: str,
        buyer_email: str,
        description: str,
    ) -> PaymentInitiation: ...

    @abstractmethod
    def parse_webhook(self, headers: Mapping[str, str], raw_body: bytes) -> WebhookEvent: ...

    @abstractmethod
    async def check(self, transaction_id: str) -> PaymentCheckResult: ...
