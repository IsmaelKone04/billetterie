"""Verrouillage Redis court (SET NX EX) pour sérialiser les achats
concurrents sur un même tarif et éviter la survente — pattern
d'idempotence/lock repris de monbail (common/idempotency/idempotency.service.ts),
porté en Python. Le contrôle de quota définitif reste fait en base (comptage
des billets déjà réservés) : Redis sert de point de sérialisation rapide, pas
de source de vérité du stock."""

import asyncio
from collections.abc import Sequence
from contextlib import AsyncExitStack, asynccontextmanager

from redis.asyncio import Redis

LOCK_TTL_SECONDS = 10
LOCK_RETRY_ATTEMPTS = 5
LOCK_RETRY_DELAY_SECONDS = 0.2


class LockAcquisitionError(Exception):
    """Le verrou n'a pas pu être acquis après plusieurs tentatives — un autre
    achat est en cours sur la même ressource, réessayer plus tard."""


def ticket_type_lock_key(ticket_type_id: int) -> str:
    return f"lock:tickettype:{ticket_type_id}"


@asynccontextmanager
async def redis_lock(redis: Redis, key: str):
    token = None
    for _ in range(LOCK_RETRY_ATTEMPTS):
        acquired = await redis.set(key, "1", nx=True, ex=LOCK_TTL_SECONDS)
        if acquired:
            token = True
            break
        await asyncio.sleep(LOCK_RETRY_DELAY_SECONDS)

    if token is None:
        raise LockAcquisitionError(key)

    try:
        yield
    finally:
        await redis.delete(key)


@asynccontextmanager
async def redis_lock_all(redis: Redis, keys: Sequence[str]):
    """Acquiert plusieurs verrous — toujours dans le même ordre trié en
    amont par l'appelant — pour éviter les interblocages entre deux achats
    concurrents portant sur les mêmes tarifs dans un ordre différent."""
    async with AsyncExitStack() as stack:
        for key in keys:
            await stack.enter_async_context(redis_lock(redis, key))
        yield
