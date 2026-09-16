import uuid

import pytest
from sqlalchemy import text

from app.database import engine
from app.services.auth import create_organizer_token


async def _signup(client, email: str, password: str = "un-mot-de-passe-solide"):
    return await client.post(
        "/organizers/signup",
        json={"display_name": "Organisateur de test", "email": email, "password": password},
    )


async def _delete_organizer_by_email(email: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM ticketing_organizer WHERE email = :email"), {"email": email}
        )


@pytest.mark.asyncio
async def test_signup_then_me(client):
    email = f"organisateur-{uuid.uuid4().hex[:8]}@example.com"
    try:
        signup_response = await _signup(client, email)
        assert signup_response.status_code == 201
        token = signup_response.json()["access_token"]

        me_response = await client.get(
            "/organizers/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        body = me_response.json()
        assert body["email"] == email
        assert body["display_name"] == "Organisateur de test"
    finally:
        await _delete_organizer_by_email(email)


@pytest.mark.asyncio
async def test_signup_duplicate_email_rejected(client):
    email = f"organisateur-{uuid.uuid4().hex[:8]}@example.com"
    try:
        first = await _signup(client, email)
        assert first.status_code == 201

        second = await _signup(client, email)
        assert second.status_code == 409
    finally:
        await _delete_organizer_by_email(email)


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(client):
    email = f"organisateur-{uuid.uuid4().hex[:8]}@example.com"
    try:
        await _signup(client, email, password="le-bon-mot-de-passe")

        wrong = await client.post(
            "/organizers/login", json={"email": email, "password": "mauvais-mot-de-passe"}
        )
        assert wrong.status_code == 401

        ok = await client.post(
            "/organizers/login", json={"email": email, "password": "le-bon-mot-de-passe"}
        )
        assert ok.status_code == 200
        assert ok.json()["access_token"]
    finally:
        await _delete_organizer_by_email(email)


@pytest.mark.asyncio
async def test_me_requires_token(client):
    response = await client.get("/organizers/me")
    assert response.status_code == 401

    response = await client.get("/organizers/me", headers={"Authorization": "Bearer pas-un-jwt"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_reflects_sales(client, catalogue):
    """L'événement `brouillon` de la fixture catalogue n'a aucun tarif : il
    doit apparaître avec quota_total=0 et fill_rate=0, sans jamais diviser
    par zéro. L'événement publié doit refléter exactement la vente simulée."""
    token = create_organizer_token(catalogue["organizer_id"])

    create_response = await client.post(
        "/orders",
        json={
            "event_id": catalogue["published_id"],
            "buyer_email": "acheteur-dashboard@example.com",
            "buyer_phone": "0700000099",
            "items": [{"ticket_type_id": catalogue["standard_ticket_type_id"], "quantity": 2}],
        },
    )
    transaction_id = create_response.json()["transaction_id"]
    pay_response = await client.post(
        "/payments/simulate", json={"transaction_id": transaction_id, "outcome": "success"}
    )
    assert pay_response.json()["outcome"] == "applique"

    dashboard_response = await client.get(
        "/organizers/me/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert dashboard_response.status_code == 200
    body = dashboard_response.json()
    assert body["total_events"] == 2
    assert body["total_tickets_sold"] == 2
    assert body["total_revenue"] == "10000.00"

    published = next(e for e in body["events"] if e["event_id"] == catalogue["published_id"])
    assert published["tickets_sold"] == 2
    assert published["quota_total"] == 120  # 100 Standard + 20 VIP
    assert published["revenue"] == "10000.00"

    draft = next(e for e in body["events"] if e["event_id"] == catalogue["draft_id"])
    assert draft["tickets_sold"] == 0
    assert draft["quota_total"] == 0
    assert draft["fill_rate"] == 0.0
