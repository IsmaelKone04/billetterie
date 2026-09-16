from domain.order_state_machine import OrderStatus, verifier_transition
from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_session
from ..models import Order, Ticket
from ..payments import get_payment_provider
from ..redis_client import redis
from ..schemas import OrderCreateIn, OrderCreateOut, OrderTicketsOut, TicketOut
from ..services.locks import LockAcquisitionError
from ..services.orders import (
    EventNotFound,
    InvalidTicketType,
    QuotaExceeded,
    SeatsUnavailable,
    create_order,
)
from ..services.qr import QrConfigError, build_qr_token

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
    except SeatsUnavailable as exc:
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


@router.get("/{transaction_id}/tickets", response_model=OrderTicketsOut)
async def get_order_tickets(
    transaction_id: str, email: EmailStr, session: AsyncSession = Depends(get_session)
):
    """« Mes billets » : pas de compte acheteur, la connaissance du
    transaction_id (reçu à l'achat) + l'e-mail utilisé sert de justificatif
    — suffisant pour un MVP, comme un lien de confirmation de commande."""
    result = await session.execute(
        select(Order)
        .where(Order.transaction_id == transaction_id)
        .options(
            selectinload(Order.event),
            selectinload(Order.tickets).selectinload(Ticket.ticket_type),
            selectinload(Order.tickets).selectinload(Ticket.seat),
        )
    )
    order = result.scalar_one_or_none()
    if order is None or order.buyer_email.lower() != email.lower():
        raise HTTPException(status_code=404, detail="Commande introuvable")

    if order.status != OrderStatus.BILLETS_EMIS.value:
        raise HTTPException(
            status_code=409, detail=f"Billets pas encore émis (statut actuel : {order.status})"
        )

    try:
        tickets = [
            TicketOut(
                id=ticket.id,
                ticket_type_name=ticket.ticket_type.name,
                status=ticket.status,
                qr_token=build_qr_token(ticket.id, ticket.qr_secret),
                seat_label=f"{ticket.seat.row}{ticket.seat.number}" if ticket.seat else None,
            )
            for ticket in order.tickets
        ]
    except QrConfigError as exc:
        raise HTTPException(status_code=503, detail="Génération des billets non configurée") from exc

    return OrderTicketsOut(
        transaction_id=order.transaction_id,
        status=order.status,
        event_title=order.event.title,
        tickets=tickets,
    )
