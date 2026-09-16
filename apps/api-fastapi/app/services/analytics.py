"""Dashboard organisateur : ventes, remplissage, revenus par événement. Un
billet compte comme « vendu » s'il appartient à une commande billets_emis et
n'est pas annulé (même exclusion que app/services/scan.py)."""

from dataclasses import dataclass
from decimal import Decimal

from domain.order_state_machine import OrderStatus
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Event, Order, Ticket, TicketType


@dataclass
class EventAnalytics:
    event_id: int
    title: str
    status: str
    tickets_sold: int
    quota_total: int
    revenue: Decimal

    @property
    def fill_rate(self) -> float:
        return round(self.tickets_sold / self.quota_total, 4) if self.quota_total else 0.0


async def organizer_dashboard(session: AsyncSession, organizer_id: int) -> list[EventAnalytics]:
    events = (
        (
            await session.execute(
                select(Event).where(Event.organizer_id == organizer_id).order_by(Event.starts_at)
            )
        )
        .scalars()
        .all()
    )
    if not events:
        return []
    event_ids = [event.id for event in events]

    quota_by_event = dict(
        (
            await session.execute(
                select(TicketType.event_id, func.coalesce(func.sum(TicketType.quota), 0))
                .where(TicketType.event_id.in_(event_ids))
                .group_by(TicketType.event_id)
            )
        ).all()
    )

    sold_by_event = dict(
        (
            await session.execute(
                select(Order.event_id, func.count(Ticket.id))
                .join(Ticket, Ticket.order_id == Order.id)
                .where(
                    Order.event_id.in_(event_ids),
                    Order.status == OrderStatus.BILLETS_EMIS.value,
                    Ticket.status != "annule",
                )
                .group_by(Order.event_id)
            )
        ).all()
    )

    revenue_by_event = dict(
        (
            await session.execute(
                select(Order.event_id, func.coalesce(func.sum(Order.amount_total), 0))
                .where(Order.event_id.in_(event_ids), Order.status == OrderStatus.BILLETS_EMIS.value)
                .group_by(Order.event_id)
            )
        ).all()
    )

    return [
        EventAnalytics(
            event_id=event.id,
            title=event.title,
            status=event.status,
            tickets_sold=sold_by_event.get(event.id, 0),
            quota_total=quota_by_event.get(event.id, 0),
            revenue=revenue_by_event.get(event.id, Decimal("0")),
        )
        for event in events
    ]
