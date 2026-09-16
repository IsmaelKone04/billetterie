import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_events_only_shows_published(client, catalogue):
    response = await client.get("/events")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert catalogue["published_id"] in ids
    assert catalogue["draft_id"] not in ids


@pytest.mark.asyncio
async def test_get_event_detail_includes_ticket_types(client, catalogue):
    response = await client.get(f"/events/{catalogue['published_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["venue"]["city"] == "Abidjan"
    names = sorted(t["name"] for t in body["ticket_types"])
    assert names == ["Standard", "VIP"]


@pytest.mark.asyncio
async def test_get_draft_event_returns_404(client, catalogue):
    response = await client.get(f"/events/{catalogue['draft_id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_unknown_event_returns_404(client):
    response = await client.get("/events/999999999")
    assert response.status_code == 404
