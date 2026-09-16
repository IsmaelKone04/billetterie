"""Tests d'intégration contre le vrai Postgres partagé avec admin-django
(voir docker-compose.yml — postgres doit tourner : `docker compose up -d
postgres`). Les données de test sont insérées en SQL brut (même schéma que
les migrations Django) puis nettoyées après chaque test."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.database import engine
from app.main import app
from app.redis_client import redis as redis_client


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    # pytest-asyncio ouvre une nouvelle boucle asyncio par test ; les pools
    # de connexions (asyncpg pour SQLAlchemy, le client Redis) sont créés au
    # niveau module et doivent donc être vidés après chaque test pour ne pas
    # réutiliser une connexion liée à une boucle déjà fermée.
    yield
    await engine.dispose()
    await redis_client.aclose()


@pytest_asyncio.fixture
async def catalogue():
    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc)

    async with engine.begin() as conn:
        user_id = (
            await conn.execute(
                text(
                    "INSERT INTO auth_user "
                    "(password, is_superuser, username, first_name, last_name, "
                    "email, is_staff, is_active, date_joined) "
                    "VALUES ('!', false, :username, '', '', '', false, true, :now) "
                    "RETURNING id"
                ),
                {"username": f"organisateur-{suffix}", "now": now},
            )
        ).scalar_one()

        organizer_id = (
            await conn.execute(
                text(
                    "INSERT INTO ticketing_organizer "
                    "(display_name, email, password_hash, phone, mobile_money_account, "
                    "created_at, user_id) "
                    "VALUES (:name, :email, '', '', '', :now, :user_id) RETURNING id"
                ),
                {
                    "name": f"Organisateur {suffix}",
                    "email": f"organisateur-{suffix}@example.com",
                    "now": now,
                    "user_id": user_id,
                },
            )
        ).scalar_one()

        venue_id = (
            await conn.execute(
                text(
                    "INSERT INTO ticketing_venue (name, city, address) "
                    "VALUES (:name, 'Abidjan', '') RETURNING id"
                ),
                {"name": f"Palais des congrès {suffix}"},
            )
        ).scalar_one()

        published_id = (
            await conn.execute(
                text(
                    "INSERT INTO ticketing_event "
                    "(title, description, starts_at, status, created_at, updated_at, "
                    "organizer_id, venue_id) "
                    "VALUES (:title, 'Description test', :starts_at, 'publie', :now, :now, "
                    ":organizer_id, :venue_id) RETURNING id"
                ),
                {
                    "title": f"Concert publié {suffix}",
                    "starts_at": now + timedelta(days=30),
                    "now": now,
                    "organizer_id": organizer_id,
                    "venue_id": venue_id,
                },
            )
        ).scalar_one()

        draft_id = (
            await conn.execute(
                text(
                    "INSERT INTO ticketing_event "
                    "(title, description, starts_at, status, created_at, updated_at, "
                    "organizer_id, venue_id) "
                    "VALUES (:title, '', :starts_at, 'brouillon', :now, :now, "
                    ":organizer_id, :venue_id) RETURNING id"
                ),
                {
                    "title": f"Brouillon {suffix}",
                    "starts_at": now + timedelta(days=30),
                    "now": now,
                    "organizer_id": organizer_id,
                    "venue_id": venue_id,
                },
            )
        ).scalar_one()

        standard_tt_id = (
            await conn.execute(
                text(
                    "INSERT INTO ticketing_tickettype "
                    "(name, price, quota, sales_start, sales_end, event_id, section_id) "
                    "VALUES ('Standard', '5000.00', 100, NULL, NULL, :event_id, NULL) "
                    "RETURNING id"
                ),
                {"event_id": published_id},
            )
        ).scalar_one()

        vip_tt_id = (
            await conn.execute(
                text(
                    "INSERT INTO ticketing_tickettype "
                    "(name, price, quota, sales_start, sales_end, event_id, section_id) "
                    "VALUES ('VIP', '25000.00', 20, NULL, NULL, :event_id, NULL) "
                    "RETURNING id"
                ),
                {"event_id": published_id},
            )
        ).scalar_one()

    yield {
        "organizer_id": organizer_id,
        "published_id": published_id,
        "draft_id": draft_id,
        "standard_ticket_type_id": standard_tt_id,
        "vip_ticket_type_id": vip_tt_id,
    }

    async with engine.begin() as conn:
        await conn.execute(
            text(
                "DELETE FROM ticketing_paymentevent WHERE order_id IN "
                "(SELECT id FROM ticketing_order WHERE event_id = ANY(:ids))"
            ),
            {"ids": [published_id, draft_id]},
        )
        await conn.execute(
            text(
                "DELETE FROM ticketing_ticket WHERE order_id IN "
                "(SELECT id FROM ticketing_order WHERE event_id = ANY(:ids))"
            ),
            {"ids": [published_id, draft_id]},
        )
        await conn.execute(
            text("DELETE FROM ticketing_order WHERE event_id = ANY(:ids)"),
            {"ids": [published_id, draft_id]},
        )
        await conn.execute(
            text("DELETE FROM ticketing_tickettype WHERE event_id = ANY(:ids)"),
            {"ids": [published_id, draft_id]},
        )
        await conn.execute(
            text("DELETE FROM ticketing_event WHERE id = ANY(:ids)"),
            {"ids": [published_id, draft_id]},
        )
        await conn.execute(text("DELETE FROM ticketing_venue WHERE id = :id"), {"id": venue_id})
        await conn.execute(
            text("DELETE FROM ticketing_organizer WHERE id = :id"), {"id": organizer_id}
        )
        await conn.execute(text("DELETE FROM auth_user WHERE id = :id"), {"id": user_id})


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
