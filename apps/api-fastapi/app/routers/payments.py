import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import PAYMENT_PROVIDER
from ..database import get_session
from ..payments import get_payment_provider
from ..payments.simulator import build_signed_webhook
from ..schemas import SimulatePaymentIn
from ..services.payments import process_webhook

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/webhook/{provider_name}")
async def payment_webhook(
    provider_name: str, request: Request, session: AsyncSession = Depends(get_session)
):
    provider = get_payment_provider()
    if provider.name != provider_name:
        raise HTTPException(status_code=404, detail="Provider inconnu ou inactif")

    raw_body = await request.body()
    outcome = await process_webhook(session, provider, dict(request.headers), raw_body)
    return {"outcome": outcome}


@router.post("/simulate", include_in_schema=False)
async def simulate_payment(
    payload: SimulatePaymentIn, session: AsyncSession = Depends(get_session)
):
    """Dev/tests uniquement (provider `simulator` actif) : déclenche un
    webhook auto-signé pour une commande donnée, sans dépendre d'un vrai
    opérateur Mobile Money."""
    if PAYMENT_PROVIDER != "simulator":
        raise HTTPException(status_code=404, detail="Non disponible hors mode simulator")

    headers, body = build_signed_webhook(
        transaction_id=payload.transaction_id,
        event_id=uuid.uuid4().hex,
        outcome=payload.outcome,
    )
    provider = get_payment_provider()
    outcome = await process_webhook(session, provider, headers, body)
    return {"outcome": outcome}
