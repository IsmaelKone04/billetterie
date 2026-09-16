"""Modèles SQLAlchemy reflétant le schéma Django
(apps/admin-django/ticketing/models.py). Django reste seul propriétaire du
schéma et des migrations — cette API ne crée ni ne modifie jamais de table,
mais lit ET écrit des lignes (Order/Ticket/PaymentEvent, catalogue en lecture
seule) sur les tables migrées par Django."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime


class Base(DeclarativeBase):
    # Toutes les colonnes datetime Django sont `timestamp with time zone`
    # (USE_TZ=True) — sans ce mapping, SQLAlchemy infère un TIMESTAMP WITHOUT
    # TIME ZONE et asyncpg refuse les datetimes timezone-aware qu'on écrit
    # (Order/Ticket/PaymentEvent).
    type_annotation_map = {datetime: DateTime(timezone=True)}


class Organizer(Base):
    __tablename__ = "ticketing_organizer"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str]


class Venue(Base):
    __tablename__ = "ticketing_venue"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    city: Mapped[str]
    address: Mapped[str]


class Event(Base):
    __tablename__ = "ticketing_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("ticketing_organizer.id"))
    venue_id: Mapped[int] = mapped_column(ForeignKey("ticketing_venue.id"))
    title: Mapped[str]
    description: Mapped[str]
    starts_at: Mapped[datetime]
    status: Mapped[str]

    organizer: Mapped["Organizer"] = relationship()
    venue: Mapped["Venue"] = relationship()
    ticket_types: Mapped[list["TicketType"]] = relationship(
        order_by="TicketType.price"
    )


class TicketType(Base):
    __tablename__ = "ticketing_tickettype"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("ticketing_event.id"))
    section_id: Mapped[int | None]
    name: Mapped[str]
    price: Mapped[Decimal]
    quota: Mapped[int]
    sales_start: Mapped[datetime | None]
    sales_end: Mapped[datetime | None]


class Order(Base):
    __tablename__ = "ticketing_order"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("ticketing_event.id"))
    buyer_email: Mapped[str]
    buyer_phone: Mapped[str]
    status: Mapped[str]
    amount_total: Mapped[Decimal]
    payment_provider: Mapped[str]
    transaction_id: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="order")


class Ticket(Base):
    __tablename__ = "ticketing_ticket"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("ticketing_order.id"))
    ticket_type_id: Mapped[int] = mapped_column(ForeignKey("ticketing_tickettype.id"))
    seat_id: Mapped[int | None]
    qr_secret: Mapped[str] = mapped_column(default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(default="valide")
    scanned_at: Mapped[datetime | None] = mapped_column(default=None)
    scanned_by_id: Mapped[int | None] = mapped_column(default=None)

    order: Mapped["Order"] = relationship(back_populates="tickets")
    ticket_type: Mapped["TicketType"] = relationship()


class PaymentEvent(Base):
    __tablename__ = "ticketing_paymentevent"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("ticketing_order.id"), default=None)
    provider: Mapped[str]
    provider_event_id: Mapped[str]
    event_type: Mapped[str]
    signature_valid: Mapped[bool]
    raw_payload: Mapped[dict] = mapped_column(JSONB)
    outcome: Mapped[str]
    received_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    processed_at: Mapped[datetime | None] = mapped_column(default=None)
