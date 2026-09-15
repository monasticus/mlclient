"""Higher-level cts service (CtsService / AsyncCtsService).

Both inherit the full ``Cts`` builder API and override the executing functions
(search, uris, values, estimate) to compile the expression tree and evaluate it.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._cts import Cts
from mlclient.functions.xqy._expr import Expr, _Window
from mlclient.services._executor import _AsyncExecutor, _SyncExecutor

Range = int | tuple[int, int]


def _ranged(expr: Expr, value: Range | None) -> Expr:
    if value is None:
        return expr
    lo, hi = (1, value) if isinstance(value, int) else value
    if lo < 1 or hi < lo:
        message = f"range bounds must satisfy 1 <= lo <= hi: {(lo, hi)}"
        raise ValueError(message)
    return _Window(expr, lo, hi)


@experimental(log_on_init=True)
class CtsService(Cts, _SyncExecutor):
    """Executes cts search, lexicon and estimate queries via ``/v1/eval``."""

    def search(
        self,
        expression: str = "/",
        query: Expr | None = None,
        *,
        options=(),
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ):
        """Run ``cts:search`` and return the parsed nodes.

        ``range`` slices the result lazily (XQuery ``[lo to hi]``): ``10`` yields
        the first ten hits, ``(11, 20)`` the next ten.
        """
        expr = _ranged(super().search(expression, query, options=options), range)
        return self._evaluate(expr, **kwargs)

    def uris(
        self, query: Expr | None = None, *, start=None, options=(),
        range: Range | None = None, **kwargs,  # noqa: A002
    ):
        """Run ``cts:uris`` and return the matching URIs; ``range`` slices lazily."""
        expr = _ranged(super().uris(query, start=start, options=options), range)
        return self._evaluate(expr, **kwargs)

    def values(
        self, references, query: Expr | None = None, *, start=None,
        options=(), **kwargs,
    ):
        """Run ``cts:values`` and return the lexicon values."""
        expr = super().values(references, query, start=start, options=options)
        return self._evaluate(expr, **kwargs)

    def estimate(self, query: Expr, **kwargs):
        """Run ``cts:estimate`` and return the fragment count."""
        return self._evaluate(super().estimate(query), **kwargs)


@experimental(log_on_init=True)
class AsyncCtsService(Cts, _AsyncExecutor):
    """Async execution of cts search, lexicon and estimate queries via ``/v1/eval``."""

    async def search(
        self,
        expression: str = "/",
        query: Expr | None = None,
        *,
        options=(),
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ):
        """Run ``cts:search`` and return the parsed nodes.

        ``range`` slices the result lazily (XQuery ``[lo to hi]``): ``10`` yields
        the first ten hits, ``(11, 20)`` the next ten.
        """
        expr = _ranged(super().search(expression, query, options=options), range)
        return await self._evaluate(expr, **kwargs)

    async def uris(
        self, query: Expr | None = None, *, start=None, options=(),
        range: Range | None = None, **kwargs,  # noqa: A002
    ):
        """Run ``cts:uris`` and return the matching URIs; ``range`` slices lazily."""
        expr = _ranged(super().uris(query, start=start, options=options), range)
        return await self._evaluate(expr, **kwargs)

    async def values(
        self, references, query: Expr | None = None, *, start=None,
        options=(), **kwargs,
    ):
        """Run ``cts:values`` and return the lexicon values."""
        expr = super().values(references, query, start=start, options=options)
        return await self._evaluate(expr, **kwargs)

    async def estimate(self, query: Expr, **kwargs):
        """Run ``cts:estimate`` and return the fragment count."""
        return await self._evaluate(super().estimate(query), **kwargs)
