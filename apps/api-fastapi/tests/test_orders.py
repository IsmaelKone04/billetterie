import pytest
from sqlalchemy import text

from app.database import engine


async def _order_status(transaction_id: str) -> str:
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT status FROM ticketing_order WHERE transaction_id = :tid"),
            {"tid": transaction_id},
        )
        return result.scalar_one()


async def _ticket_count(transaction_id: str) -> int:
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT count(*) FROM ticketing_ticket t "
                "JOIN ticketing_order o ON o.id = t.order_id "
                "WHERE o.transaction_id = :tid"
            ),
            {"tid": transaction_id},
        )
        return result.scalar_one()


@pytest.mark.asyncio
async def test_create_order_reserves_tickets_and_awaits_payment(client, catalogue):
    response = await client.post(
        "/orders",
        json={
            "event_id": catalogue["published_id"],
            "buyer_email": "acheteur@example.com",
            "buyer_phone": "0700000001",
            "items": [{"ticket_type_id": catalogue["standard_ticket_type_id"], "quantity": 2}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "paiement_en_attente"
    assert body["amount_total"] == "10000.00"

    assert await _ticket_count(body["transaction_id"]) == 2


@pytest.mark.asyncio
async def test_quota_exceeded_returns_409(client, catalogue):
    response = await client.post(
        "/orders",
        json={
            "event_id": catalogue["published_id"],
            "buyer_email": "acheteur@example.com",
            "buyer_phone": "0700000002",
            "items": [{"ticket_type_id": catalogue["vip_ticket_type_id"], "quantity": 21}],
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_unknown_event_returns_404(client, catalogue):
    response = await client.post(
        "/orders",
        json={
            "event_id": 999999999,
            "buyer_email": "acheteur@example.com",
            "buyer_phone": "0700000003",
            "items": [{"ticket_type_id": catalogue["standard_ticket_type_id"], "quantity": 1}],
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_successful_payment_emits_tickets(client, catalogue):
    create_response = await client.post(
        "/orders",
        json={
            "event_id": catalogue["published_id"],
            "buyer_email": "acheteur@example.com",
            "buyer_phone": "0700000004",
            "items": [{"ticket_type_id": catalogue["standard_ticket_type_id"], "quantity": 1}],
        },
    )
    transaction_id = create_response.json()["transaction_id"]

    pay_response = await client.post(
        "/payments/simulate", json={"transaction_id": transaction_id, "outcome": "success"}
    )
    assert pay_response.status_code == 200
    assert pay_response.json()["outcome"] == "applique"
    assert await _order_status(transaction_id) == "billets_emis"

    # Rejouer la même notification doit être sans effet (idempotence).
    replay_response = await client.post(
        "/payments/simulate", json={"transaction_id": transaction_id, "outcome": "success"}
    )
    assert replay_response.json()["outcome"] == "ignore"
    assert await _order_status(transaction_id) == "billets_emis"


@pytest.mark.asyncio
async def test_failed_payment_marks_order_echouee(client, catalogue):
    create_response = await client.post(
        "/orders",
        json={
            "event_id": catalogue["published_id"],
            "buyer_email": "acheteur@example.com",
            "buyer_phone": "0700000005",
            "items": [{"ticket_type_id": catalogue["standard_ticket_type_id"], "quantity": 1}],
        },
    )
    transaction_id = create_response.json()["transaction_id"]

    pay_response = await client.post(
        "/payments/simulate", json={"transaction_id": transaction_id, "outcome": "failed"}
    )
    assert pay_response.json()["outcome"] == "applique"
    assert await _order_status(transaction_id) == "echouee"


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature(client):
    response = await client.post(
        "/payments/webhook/simulator",
        content=b'{"transaction_id": "unknown", "event_id": "x", "status": "ACCEPTED"}',
        headers={
            "x-simulator-timestamp": "123",
            "x-simulator-signature": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    )
    assert response.status_code == 200
    assert response.json()["outcome"] == "signature_invalide"

    # Pas de commande associée (order_id NULL) : hors périmètre du fixture
    # `catalogue`, on nettoie explicitement pour ne rien laisser en base.
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM ticketing_paymentevent WHERE outcome = 'signature_invalide'")
        )
