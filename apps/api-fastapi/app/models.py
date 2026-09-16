"""Modèles SQLAlchemy en lecture seule, reflétant le schéma Django
(apps/admin-django/ticketing/models.py). Django reste seul propriétaire du
schéma et des migrations — cette API ne crée ni ne modifie jamais de table."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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
