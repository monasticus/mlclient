"""Evaluate one query across databases with bounded async HTTP concurrency."""

import asyncio
from itertools import islice

import httpx

from mlclient import MLClientManager


async def evaluate(environment, connection, databases, query_file, *, concurrency=8):
    """Run independent evaluations in bounded batches and clean up failures.

    Parameters
    ----------
    environment, connection : str
        Configured environment and REST connection identifiers.
    databases : iterable of str
        Databases in which to run the query.
    query_file : str
        Local query-only .xqy/.sjs file evaluated independently in each database.
    concurrency : int, default 8
        Maximum tasks and connections in one batch.

    Returns
    -------
    dict
        Results by database, in input order.

    Raises
    ------
    ValueError
        If concurrency is not positive.
    Exception
        If an evaluation fails, after outstanding tasks have been cancelled.
    """
    if concurrency < 1:
        message = "concurrency must be positive"
        raise ValueError(message)
    remaining = iter(databases)
    results = {}
    manager = MLClientManager(environment)
    async with manager.get_async_client(
        connection,
        limits=httpx.Limits(max_connections=concurrency),
    ) as ml:
        while batch := list(islice(remaining, concurrency)):
            tasks = [
                asyncio.create_task(ml.eval.file(query_file, database=db))
                for db in batch
            ]
            try:
                values = await asyncio.gather(*tasks)
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            results.update(zip(batch, values))
    return results
