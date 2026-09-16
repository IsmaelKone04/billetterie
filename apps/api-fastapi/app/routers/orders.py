from domain.order_state_machine import OrderStatus, verifier_transition
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..payments import get_payment_provider
from ..redis_client import redis
from ..schemas import OrderCreateIn, OrderCreateOut
from ..services.locks import LockAcquisitionError
from ..services.orders import EventNotFound, InvalidTicketType, QuotaExceeded, create_order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderCreateOut, status_code=201)
async def create_order_endpoint(
    payload: OrderCreateIn, session: AsyncSession = Depends(get_session)
):
    try:
        order = await create_order(session, redis, payload)
    except EventNotFound as exc:
        raise HTTPException(status_code=404, detail="Événement introuvable ou non publié") from exc
    except InvalidTicketType as exc:
        raise HTTPException(status_code=400, detail="Tarif invalide pour cet événement") from exc
    except QuotaExceeded as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LockAcquisitionError as exc:
        raise HTTPException(
            status_code=409, detail="Achat concurrent en cours sur ce tarif, réessayez."
        ) from exc

    provider = get_payment_provider()
    verifier_transition(OrderStatus(order.status), OrderStatus.PAIEMENT_EN_ATTENTE)
    order.status = OrderStatus.PAIEMENT_EN_ATTENTE.value
    order.payment_provider = provider.name
    await session.commit()

    try:
        initiation = await provider.initiate(
            transaction_id=order.transaction_id,
            amount=order.amount_total,
            buyer_phone=order.buyer_phone,
            buyer_email=order.buyer_email,
            description=f"billetterie - commande {order.transaction_id}",
        )
    except Exception as exc:
        verifier_transition(OrderStatus(order.status), OrderStatus.ECHOUEE)
        order.status = OrderStatus.ECHOUEE.value
        await session.commit()
        raise HTTPException(status_code=502, detail="Initiation du paiement impossible") from exc

    return OrderCreateOut(
        order_id=order.id,
        transaction_id=order.transaction_id,
        status=order.status,
        amount_total=order.amount_total,
        payment_url=initiation.payment_url,
    )
