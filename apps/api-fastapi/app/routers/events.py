from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_session
from ..models import Event
from ..schemas import EventDetailOut, EventListItemOut, TicketTypeOut, VenueOut

router = APIRouter(prefix="/events", tags=["events"])

# Valeur exacte de Event.Statut.PUBLIE côté Django
# (apps/admin-django/ticketing/models.py) — seuls les événements publiés
# sont visibles sur le catalogue public.
PUBLISHED_STATUS = "publie"


def _to_list_item(event: Event) -> EventListItemOut:
    return EventListItemOut(
        id=event.id,
        title=event.title,
        starts_at=event.starts_at,
        venue=VenueOut(name=event.venue.name, city=event.venue.city),
        organizer_display_name=event.organizer.display_name,
    )


@router.get("", response_model=list[EventListItemOut])
async def list_events(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Event)
        .where(Event.status == PUBLISHED_STATUS)
        .options(selectinload(Event.venue), selectinload(Event.organizer))
        .order_by(Event.starts_at)
    )
    return [_to_list_item(event) for event in result.scalars()]


@router.get("/{event_id}", response_model=EventDetailOut)
async def get_event(event_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Event)
        .where(Event.id == event_id, Event.status == PUBLISHED_STATUS)
        .options(
            selectinload(Event.venue),
            selectinload(Event.organizer),
            selectinload(Event.ticket_types),
        )
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=404, detail="Événement introuvable")

    item = _to_list_item(event)
    return EventDetailOut(
        **item.model_dump(),
        description=event.description,
        ticket_types=[
            TicketTypeOut(id=t.id, name=t.name, price=t.price, quota=t.quota)
            for t in event.ticket_types
        ],
    )
