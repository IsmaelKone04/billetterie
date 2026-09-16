from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Organizer
from ..schemas import (
    EventAnalyticsOut,
    OrganizerAuthOut,
    OrganizerDashboardOut,
    OrganizerLoginIn,
    OrganizerMeOut,
    OrganizerSignupIn,
)
from ..services.analytics import organizer_dashboard
from ..services.auth import (
    AuthConfigError,
    create_organizer_token,
    decode_organizer_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/organizers", tags=["organizers"])


async def get_current_organizer(
    authorization: str = Header(default=""), session: AsyncSession = Depends(get_session)
) -> Organizer:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authentification requise")

    organizer_id = decode_organizer_token(token)
    if organizer_id is None:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    organizer = await session.get(Organizer, organizer_id)
    if organizer is None:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return organizer


@router.post("/signup", response_model=OrganizerAuthOut, status_code=201)
async def signup(payload: OrganizerSignupIn, session: AsyncSession = Depends(get_session)):
    """Inscription en libre-service — voir app/services/auth.py pour le
    hachage du mot de passe (PBKDF2, jamais en clair en base)."""
    organizer = Organizer(
        display_name=payload.display_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        mobile_money_account=payload.mobile_money_account,
    )
    session.add(organizer)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Cet e-mail est déjà utilisé") from exc

    try:
        token = create_organizer_token(organizer.id)
    except AuthConfigError as exc:
        raise HTTPException(status_code=503, detail="Authentification non configurée") from exc
    return OrganizerAuthOut(access_token=token)


@router.post("/login", response_model=OrganizerAuthOut)
async def login(payload: OrganizerLoginIn, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Organizer).where(Organizer.email == payload.email.lower())
    )
    organizer = result.scalar_one_or_none()
    if organizer is None or not verify_password(payload.password, organizer.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou mot de passe incorrect")

    try:
        token = create_organizer_token(organizer.id)
    except AuthConfigError as exc:
        raise HTTPException(status_code=503, detail="Authentification non configurée") from exc
    return OrganizerAuthOut(access_token=token)


@router.get("/me", response_model=OrganizerMeOut)
async def me(organizer: Organizer = Depends(get_current_organizer)):
    return OrganizerMeOut(id=organizer.id, display_name=organizer.display_name, email=organizer.email)


@router.get("/me/dashboard", response_model=OrganizerDashboardOut)
async def dashboard(
    organizer: Organizer = Depends(get_current_organizer),
    session: AsyncSession = Depends(get_session),
):
    events = await organizer_dashboard(session, organizer.id)
    return OrganizerDashboardOut(
        organizer_id=organizer.id,
        display_name=organizer.display_name,
        total_events=len(events),
        total_tickets_sold=sum(event.tickets_sold for event in events),
        total_revenue=sum((event.revenue for event in events), start=Decimal("0")),
        events=[
            EventAnalyticsOut(
                event_id=event.event_id,
                title=event.title,
                status=event.status,
                tickets_sold=event.tickets_sold,
                quota_total=event.quota_total,
                fill_rate=event.fill_rate,
                revenue=event.revenue,
            )
            for event in events
        ],
    )
