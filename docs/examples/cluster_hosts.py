"""Run one query on every host of a cluster under a shared concurrency cap."""

import asyncio

from mlclient import AsyncMLClient
from mlclient.http import HTTPConfig


async def eval_on_each_host(
    hosts: list[str],
    xquery: str,
    *,
    max_in_flight: int = 4,
) -> dict[str, str]:
    """Evaluate a query against each host, capping how many run at once.

    Each host needs its own client, so each has its own connection pool -
    pool limits bound a single client, not the aggregate across clients. One
    shared semaphore caps how many hosts are queried concurrently.
    """
    base = HTTPConfig.resolve(port=8000)
    semaphore = asyncio.Semaphore(max_in_flight)

    async def eval_on(host):
        async with semaphore, AsyncMLClient(config=base.clone(host=host)) as ml:
            return host, await ml.eval.xquery(xquery)

    return dict(await asyncio.gather(*(eval_on(host) for host in hosts)))
