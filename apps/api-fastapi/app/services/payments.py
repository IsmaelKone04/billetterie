"""Application des résultats de paiement (webhook + `check` CinetPay pour
les providers qui l'exigent) : transitions de la commande via la machine à
états partagée, journal d'audit `PaymentEvent` avec déduplication par
`provider_event_id` — pattern repris de monbail
(payment-webhook.service.ts / PaymentEvent Prisma)."""

import uuid
from datetime import datetime, timezone

from domain.order_state_machine import OrderStatus, verifier_transition
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Order, PaymentEvent
from ..payments.base import PaymentProvider


async def _already_processed(session: AsyncSession, provider_event_id: str) -> bool:
    result = await session.execute(
        select(PaymentEvent).where(PaymentEvent.provider_event_id == provider_event_id)
    )
    return result.scalar_one_or_none() is not None


async def _record_event(
    session: AsyncSession,
    *,
    order_id: int | None,
    provider: str,
    provider_event_id: str,
    event_type: str,
    signature_valid: bool,
    raw_payload: dict,
    outcome: str,
    processed: bool = False,
) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        PaymentEvent(
            order_id=order_id,
            provider=provider,
            provider_event_id=provider_event_id,
            event_type=event_type,
            signature_valid=signature_valid,
            raw_payload=raw_payload,
            outcome=outcome,
            received_at=now,
            processed_at=now if processed else None,
        )
    )
    await session.commit()


def _apply_outcome(order: Order, outcome_status: str) -> None:
    if outcome_status == "success":
        verifier_transition(OrderStatus(order.status), OrderStatus.PAYEE)
        order.status = OrderStatus.PAYEE.value
        verifier_transition(OrderStatus(order.status), OrderStatus.BILLETS_EMIS)
        order.status = OrderStatus.BILLETS_EMIS.value
    else:
        verifier_transition(OrderStatus(order.status), OrderStatus.ECHOUEE)
        order.status = OrderStatus.ECHOUEE.value
    order.updated_at = datetime.now(timezone.utc)


async def process_webhook(
    session: AsyncSession,
    provider: PaymentProvider,
    headers: dict[str, str],
    raw_body: bytes,
) -> str:
    """Retourne l'issue : 'applique', 'ignore', 'rejete' ou
    'signature_invalide'."""
    event = provider.parse_webhook(headers, raw_body)

    if not event.signature_valid:
        await _record_event(
            session,
            order_id=None,
            provider=provider.name,
            provider_event_id=f"{provider.name}:signature_invalide:{uuid.uuid4().hex}",
            event_type=event.event_type,
            signature_valid=False,
            raw_payload=event.raw_payload,
            outcome="signature_invalide",
        )
        return "signature_invalide"

    result = await session.execute(
        select(Order).where(Order.transaction_id == event.transaction_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        await _record_event(
            session,
            order_id=None,
            provider=provider.name,
            provider_event_id=f"{provider.name}:commande_inconnue:{uuid.uuid4().hex}",
            event_type=event.event_type,
            signature_valid=True,
            raw_payload=event.raw_payload,
            outcome="rejete",
        )
        return "rejete"

    if provider.requires_check:
        check_result = await provider.check(event.transaction_id)
        outcome_status = check_result.status
    else:
        outcome_status = "success" if event.event_type == "payment.accepted" else "failed"

    if outcome_status == "pending":
        await _record_event(
            session,
            order_id=order.id,
            provider=provider.name,
            provider_event_id=f"{provider.name}:{event.transaction_id}:pending:{uuid.uuid4().hex}",
            event_type=event.event_type,
            signature_valid=True,
            raw_payload=event.raw_payload,
            outcome="ignore",
        )
        return "ignore"

    provider_event_id = f"{provider.name}:{event.transaction_id}:{outcome_status}"
    if await _already_processed(session, provider_event_id):
        # Notification déjà appliquée (retry du provider) — idempotent.
        return "ignore"

    _apply_outcome(order, outcome_status)
    await _record_event(
        session,
        order_id=order.id,
        provider=provider.name,
        provider_event_id=provider_event_id,
        event_type=event.event_type,
        signature_valid=True,
        raw_payload=event.raw_payload,
        outcome="applique",
        processed=True,
    )
    return "applique"
