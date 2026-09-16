"""Shared execution through the public expression evaluator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mlclient.services.eval import AsyncEvalService, EvalService

if TYPE_CHECKING:
    from mlclient.api.rest import AsyncRestApi, RestApi
    from mlclient.functions import Expr


class _SyncExecutor:
    """Delegate expression execution to EvalService."""

    def __init__(self, rest: RestApi):
        self._eval = EvalService(rest)

    def _evaluate(self, expr: Expr, **kwargs) -> list:
        return self._eval.expression(expr, **kwargs)


class _AsyncExecutor:
    """Delegate expression execution to AsyncEvalService."""

    def __init__(self, rest: AsyncRestApi):
        self._eval = AsyncEvalService(rest)

    async def _evaluate(self, expr: Expr, **kwargs) -> list:
        return await self._eval.expression(expr, **kwargs)


def _single(items: list):
    """Enforce the exactly-one-item contract of aggregate conveniences."""
    if len(items) != 1:
        message = "expected exactly one result item"
        raise ValueError(message)
    return items[0]
