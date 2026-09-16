import pytest
from sqlalchemy import text

from app.database import engine


async def _issue_order(client, catalogue, buyer_email: str) -> str:
    """Crée une commande puis simule un paiement réussi — retourne le
    transaction_id d'une commande billets_emis, prête pour les tests
    "mes billets"/scan."""
    create_response = await client.post(
        "/orders",
        json={
            "event_id": catalogue["published_id"],
            "buyer_email": buyer_email,
            "buyer_phone": "0700000010",
            "items": [{"ticket_type_id": catalogue["standard_ticket_type_id"], "quantity": 1}],
        },
    )
    transaction_id = create_response.json()["transaction_id"]

    pay_response = await client.post(
        "/payments/simulate", json={"transaction_id": transaction_id, "outcome": "success"}
    )
    assert pay_response.json()["outcome"] == "applique"
    return transaction_id


async def _reset_ticket_status(ticket_id: int) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE ticketing_ticket SET status = 'valide', scanned_at = NULL WHERE id = :id"),
            {"id": ticket_id},
        )


@pytest.mark.asyncio
async def test_my_tickets_requires_matching_email(client, catalogue):
    transaction_id = await _issue_order(client, catalogue, "acheteur-scan1@example.com")

    wrong_email = await client.get(
        f"/orders/{transaction_id}/tickets", params={"email": "quelquun-dautre@example.com"}
    )
    assert wrong_email.status_code == 404

    ok = await client.get(
        f"/orders/{transaction_id}/tickets", params={"email": "acheteur-scan1@example.com"}
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "billets_emis"
    assert len(body["tickets"]) == 1
    assert body["tickets"][0]["qr_token"]


@pytest.mark.asyncio
async def test_my_tickets_pending_order_returns_409(client, catalogue):
    create_response = await client.post(
        "/orders",
        json={
            "event_id": catalogue["published_id"],
            "buyer_email": "acheteur-scan2@example.com",
            "buyer_phone": "0700000011",
            "items": [{"ticket_type_id": catalogue["standard_ticket_type_id"], "quantity": 1}],
        },
    )
    transaction_id = create_response.json()["transaction_id"]

    response = await client.get(
        f"/orders/{transaction_id}/tickets", params={"email": "acheteur-scan2@example.com"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_scan_accepts_then_rejects_duplicate(client, catalogue):
    transaction_id = await _issue_order(client, catalogue, "acheteur-scan3@example.com")
    tickets_response = await client.get(
        f"/orders/{transaction_id}/tickets", params={"email": "acheteur-scan3@example.com"}
    )
    ticket = tickets_response.json()["tickets"][0]

    first_scan = await client.post(
        "/scan",
        json={"qr_token": ticket["qr_token"]},
        headers={"X-Scan-Key": "insecure-dev-only-scan-key-do-not-use-in-production"},
    )
    assert first_scan.status_code == 200
    assert first_scan.json()["ticket_id"] == ticket["id"]

    second_scan = await client.post(
        "/scan",
        json={"qr_token": ticket["qr_token"]},
        headers={"X-Scan-Key": "insecure-dev-only-scan-key-do-not-use-in-production"},
    )
    assert second_scan.status_code == 409
    assert "déjà scanné" in second_scan.json()["detail"]

    await _reset_ticket_status(ticket["id"])


@pytest.mark.asyncio
async def test_scan_rejects_wrong_key(client, catalogue):
    transaction_id = await _issue_order(client, catalogue, "acheteur-scan4@example.com")
    tickets_response = await client.get(
        f"/orders/{transaction_id}/tickets", params={"email": "acheteur-scan4@example.com"}
    )
    ticket = tickets_response.json()["tickets"][0]

    response = await client.post(
        "/scan", json={"qr_token": ticket["qr_token"]}, headers={"X-Scan-Key": "mauvaise-cle"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_scan_rejects_forged_token(client, catalogue):
    transaction_id = await _issue_order(client, catalogue, "acheteur-scan5@example.com")
    tickets_response = await client.get(
        f"/orders/{transaction_id}/tickets", params={"email": "acheteur-scan5@example.com"}
    )
    ticket = tickets_response.json()["tickets"][0]
    forged = f"{ticket['id']}.dGFtcGVyZWQ"

    response = await client.post(
        "/scan",
        json={"qr_token": forged},
        headers={"X-Scan-Key": "insecure-dev-only-scan-key-do-not-use-in-production"},
    )
    assert response.status_code == 400
