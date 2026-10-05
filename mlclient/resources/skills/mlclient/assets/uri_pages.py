"""Read URI lexicon pages with pure Python builders and an inclusive cursor."""

from __future__ import annotations

from collections.abc import AsyncIterator

from mlclient import AsyncMLClient
from mlclient.functions.xqy import XqyExpression, cts


async def uri_pages(
    ml: AsyncMLClient,
    query: XqyExpression,
    *,
    batch_size: int = 1000,
    forest_ids: list[int] | None = None,
    database: str | None = None,
) -> AsyncIterator[list[str]]:
    """Yield bounded batches without materializing all matching URIs.

    Parameters
    ----------
    ml : AsyncMLClient
        An open client; its lifecycle remains with the caller.
    query : XqyExpression
        CTS builder expression, not a string of XQuery source.
    batch_size : int
        Positive number of entries to emit per batch.
    forest_ids : list[int] or None
        Fixed nonempty primary-forest partition, or None for the whole database.
    database : str or None
        Target database; None uses the App Server's content database.

    Yields
    ------
    list[str]
        At most batch_size URI lexicon candidates in ascending item order.

    Raises
    ------
    ValueError
        If batch size or forest scope is invalid, or the cursor does not advance.
    TypeError
        If query is not a builder or the server returns non-string URI values.
    Exception
        Propagates server/transport failures; no partial result is labelled complete.
    """
    if not isinstance(query, XqyExpression):
        message = "query must be a CTS builder expression"
        raise TypeError(message)
    if (
        not isinstance(batch_size, int)
        or isinstance(batch_size, bool)
        or batch_size < 1
        or forest_ids == []
    ):
        message = "batch_size must be positive and forest_ids must not be empty"
        raise ValueError(message)
    cursor = ""
    while True:
        expression = cts.uris(
            start=cursor,
            options=["document", "item-order", "ascending"],
            query=query,
            quality_weight=1.0,
            forest_ids=forest_ids,
        ).pos([1, batch_size + 1])
        values = await ml.eval.expression(expression, database=database)
        values = values if isinstance(values, list) else [values]
        if any(not isinstance(uri, str) for uri in values):
            message = "URI lexicon returned a non-string value"
            raise TypeError(message)
        more = len(values) > batch_size
        if more and values[batch_size] == cursor:
            message = "URI lexicon cursor did not advance"
            raise ValueError(message)
        if values:
            yield values[:batch_size]
        if not more:
            break
        cursor = values[batch_size]
