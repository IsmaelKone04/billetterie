from ..config import PAYMENT_PROVIDER
from .base import PaymentProvider
from .cinetpay import CinetPayProvider
from .simulator import SimulatorProvider

_PROVIDERS: dict[str, PaymentProvider] = {
    "simulator": SimulatorProvider(),
    "cinetpay": CinetPayProvider(),
}


def get_payment_provider() -> PaymentProvider:
    try:
        return _PROVIDERS[PAYMENT_PROVIDER]
    except KeyError as exc:
        raise RuntimeError(
            f"PAYMENT_PROVIDER={PAYMENT_PROVIDER!r} inconnu "
            f"(valeurs valides : {sorted(_PROVIDERS)})"
        ) from exc
