from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class VenueOut(BaseModel):
    name: str
    city: str


class TicketTypeOut(BaseModel):
    id: int
    name: str
    price: Decimal
    quota: int


class EventListItemOut(BaseModel):
    id: int
    title: str
    starts_at: datetime
    venue: VenueOut
    organizer_display_name: str


class EventDetailOut(EventListItemOut):
    description: str
    ticket_types: list[TicketTypeOut]
