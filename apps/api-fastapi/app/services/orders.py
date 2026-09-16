"""Création de commande : validation du panier, verrouillage Redis
anti-survente (un verrou court par tarif, TTL 10 s), contrôle du quota en
base, puis réservation immédiate des billets (créés dès la commande, avant
paiement — c'est ce qui "retient" le stock pendant la fenêtre de paiement)."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from domain.order_state_machine import OrderStatus
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Event, Order, Seat, Section, Ticket, TicketType
from ..schemas import OrderCreateIn
from .locks import redis_lock_all, ticket_type_lock_key

PUBLISHED_STATUS = "publie"

# Statuts de commande qui retiennent encore du stock (pas libéré). Une
# commande ECHOUEE/ANNULEE/REMBOURSEE ne compte plus dans le quota consommé.
RESERVING_STATUSES = [
    OrderStatus.CREEE.value,
    OrderStatus.PAIEMENT_EN_ATTENTE.value,
    OrderStatus.PAYEE.value,
    OrderStatus.BILLETS_EMIS.value,
]


class EventNotFound(Exception):
    pass


class InvalidTicketType(Exception):
    pass


class QuotaExceeded(Exception):
    def __init__(self, ticket_type_name: str):
        self.ticket_type_name = ticket_type_name
        super().__init__(f"Quota insuffisant pour « {ticket_type_name} »")


class SeatsUnavailable(Exception):
    def __init__(self, section_name: str):
        self.section_name = section_name
        super().__init__(f"Plus assez de sièges libres dans la section « {section_name} »")


async def create_order(session: AsyncSession, redis: Redis, payload: OrderCreateIn) -> Order:
    event = await session.get(Event, payload.event_id)
    if event is None or event.status != PUBLISHED_STATUS:
        raise EventNotFound()

    ticket_type_ids = {item.ticket_type_id for item in payload.items}
    result = await session.execute(select(TicketType).where(TicketType.id.in_(ticket_type_ids)))
    ticket_types_by_id = {tt.id: tt for tt in result.scalars()}

    quantities: dict[int, int] = {}
    for item in payload.items:
        ticket_type = ticket_types_by_id.get(item.ticket_type_id)
        if ticket_type is None or ticket_type.event_id != event.id:
            raise InvalidTicketType()
        quantities[item.ticket_type_id] = quantities.get(item.ticket_type_id, 0) + item.quantity

    # Ordre trié : deux achats concurrents sur les mêmes tarifs acquièrent
    # toujours les verrous dans le même ordre (pas d'interblocage).
    lock_keys = [ticket_type_lock_key(tt_id) for tt_id in sorted(quantities)]

    async with redis_lock_all(redis, lock_keys):
        for tt_id, requested_qty in quantities.items():
            reserved = await session.scalar(
                select(func.count())
                .select_from(Ticket)
                .join(Order, Ticket.order_id == Order.id)
                .where(Ticket.ticket_type_id == tt_id, Order.status.in_(RESERVING_STATUSES))
            )
            if reserved + requested_qty > ticket_types_by_id[tt_id].quota:
                raise QuotaExceeded(ticket_types_by_id[tt_id].name)

        # Sièges numérotés : un siège par billet, réservé dès la commande
        # (comme le quota), jamais réattribué tant que la commande qui le
        # retient n'est pas échouée/annulée/remboursée. Portée par
        # (section, événement) : une même section peut être revendue pour
        # un autre événement au même lieu sans conflit.
        seats_by_ticket_type: dict[int, list[int]] = {}
        section_ids = {
            ticket_types_by_id[tt_id].section_id
            for tt_id in quantities
            if ticket_types_by_id[tt_id].section_id is not None
        }
        if section_ids:
            sections_result = await session.execute(
                select(Section).where(Section.id.in_(section_ids))
            )
            numbered_section_ids = {
                s.id: s.name for s in sections_result.scalars() if s.has_numbered_seats
            }
            for section_id, section_name in numbered_section_ids.items():
                requested_for_section = sum(
                    qty
                    for tt_id, qty in quantities.items()
                    if ticket_types_by_id[tt_id].section_id == section_id
                )
                taken_result = await session.execute(
                    select(Ticket.seat_id)
                    .join(TicketType, Ticket.ticket_type_id == TicketType.id)
                    .join(Order, Ticket.order_id == Order.id)
                    .where(
                        TicketType.section_id == section_id,
                        TicketType.event_id == event.id,
                        Order.status.in_(RESERVING_STATUSES),
                        Ticket.seat_id.is_not(None),
                    )
                )
                taken_ids = {row[0] for row in taken_result}
                available_result = await session.execute(
                    select(Seat.id)
                    .where(Seat.section_id == section_id, Seat.id.not_in(taken_ids))
                    .order_by(Seat.row, Seat.number)
                )
                available_ids = [row[0] for row in available_result]
                if len(available_ids) < requested_for_section:
                    raise SeatsUnavailable(section_name)

                cursor = iter(available_ids)
                for tt_id, qty in quantities.items():
                    if ticket_types_by_id[tt_id].section_id == section_id:
                        seats_by_ticket_type[tt_id] = [next(cursor) for _ in range(qty)]

        now = datetime.now(timezone.utc)
        amount_total: Decimal = sum(
            (ticket_types_by_id[tt_id].price * qty for tt_id, qty in quantities.items()),
            start=Decimal("0"),
        )

        order = Order(
            event_id=event.id,
            buyer_email=payload.buyer_email,
            buyer_phone=payload.buyer_phone,
            status=OrderStatus.CREEE.value,
            amount_total=amount_total,
            payment_provider="",
            transaction_id=f"BILLETTERIE-{uuid.uuid4().hex}",
            created_at=now,
            updated_at=now,
        )
        session.add(order)
        await session.flush()

        for tt_id, qty in quantities.items():
            seat_ids = seats_by_ticket_type.get(tt_id)
            for i in range(qty):
                session.add(
                    Ticket(
                        order_id=order.id,
                        ticket_type_id=tt_id,
                        seat_id=seat_ids[i] if seat_ids else None,
                        qr_secret=str(uuid.uuid4()),
                        status="valide",
                    )
                )

        await session.commit()

    return order
