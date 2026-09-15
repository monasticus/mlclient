"""Count documents in a small set of databases using independent eval requests."""

import asyncio

import httpx

from mlclient import AsyncMLClient


async def count_documents(databases: list[str]) -> dict[str, int]:
    """Return document counts, allowing up to four evaluations at a time."""
    limits = httpx.Limits(max_connections=4)
    async with AsyncMLClient(limits=limits) as ml:

        async def count_one(database):
            count = await ml.eval.xquery(
                "fn:count(fn:collection())",
                database=database,
            )
            return database, count

        return dict(await asyncio.gather(*(count_one(name) for name in databases)))
