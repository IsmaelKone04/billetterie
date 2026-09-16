"""Scan d'un billet à l'entrée : vérifie le token QR signé, refuse tout
billet dont la commande n'est pas billets_emis, marque le billet scanné, et
refuse explicitement un second scan en renvoyant l'heure du premier
(anti-duplication — un billet ne peut faire entrer qu'une seule personne)."""

from dataclasses import dataclass
from datetime import datetime, timezone

from domain.order_state_machine import OrderStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Ticket, TicketType
from .qr import parse_ticket_id, verify_qr_token

VALIDE = "valide"
SCANNE = "scanne"
ANNULE = "annule"


class InvalidQrToken(Exception):
    pass


@dataclass
class ScanResult:
    ticket_id: int
    ticket_type_name: str
    event_title: str
    already_scanned: bool
    scanned_at: datetime | None


async def scan_ticket(session: AsyncSession, token: str) -> ScanResult:
    ticket_id = parse_ticket_id(token)
    if ticket_id is None:
        raise InvalidQrToken()

    result = await session.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(
            selectinload(Ticket.ticket_type).selectinload(TicketType.event),
            selectinload(Ticket.order),
        )
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise InvalidQrToken()

    if not verify_qr_token(token, ticket.id, ticket.qr_secret):
        raise InvalidQrToken()

    if ticket.order.status != OrderStatus.BILLETS_EMIS.value or ticket.status == ANNULE:
        # Commande jamais finalisée (paiement pas encore confirmé) ou billet
        # annulé (remboursement) : jamais un billet scannable.
        raise InvalidQrToken()

    ticket_type = ticket.ticket_type
    result_data = ScanResult(
        ticket_id=ticket.id,
        ticket_type_name=ticket_type.name,
        event_title=ticket_type.event.title,
        already_scanned=ticket.status == SCANNE,
        scanned_at=ticket.scanned_at,
    )
    if result_data.already_scanned:
        return result_data

    ticket.status = SCANNE
    ticket.scanned_at = datetime.now(timezone.utc)
    await session.commit()
    result_data.scanned_at = ticket.scanned_at
    return result_data
