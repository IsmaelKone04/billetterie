from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


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


class OrderItemIn(BaseModel):
    ticket_type_id: int
    quantity: int = Field(gt=0, le=50)


class OrderCreateIn(BaseModel):
    event_id: int
    buyer_email: EmailStr
    buyer_phone: str = Field(min_length=8, max_length=30)
    items: list[OrderItemIn] = Field(min_length=1)


class OrderCreateOut(BaseModel):
    order_id: int
    transaction_id: str
    status: str
    amount_total: Decimal
    payment_url: str | None


class SimulatePaymentIn(BaseModel):
    transaction_id: str
    outcome: str = Field(pattern="^(success|failed)$")


class TicketOut(BaseModel):
    id: int
    ticket_type_name: str
    status: str
    qr_token: str


class OrderTicketsOut(BaseModel):
    transaction_id: str
    status: str
    event_title: str
    tickets: list[TicketOut]


class ScanIn(BaseModel):
    qr_token: str


class ScanOut(BaseModel):
    ticket_id: int
    ticket_type_name: str
    event_title: str
    scanned_at: datetime
