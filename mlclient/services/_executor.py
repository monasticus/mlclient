"""Shared plumbing for services that compile and evaluate ``Expr`` trees.

Each namespace service (cts, fn, xdmp) inherits its builder namespace for the
API and one of these executors for the ``/v1/eval`` round-trip. Every runtime
value is passed as an external variable, so no value is interpolated into the
XQuery source.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mlclient.functions.xqy._expr import Expr
from mlclient.models.version import MarkLogicVersion
from mlclient.services.eval import AsyncEvalService, EvalService

if TYPE_CHECKING:
    from mlclient.api.rest import AsyncRestApi, RestApi

_LATEST_VERSION = MarkLogicVersion("12.0")


def _coerce_version(version: str | MarkLogicVersion | None) -> MarkLogicVersion:
    if version is None:
        return _LATEST_VERSION
    if isinstance(version, MarkLogicVersion):
        return version
    return MarkLogicVersion(version)


def _verify_version(expr: Expr, version: MarkLogicVersion) -> None:
    supported = version.parts[0]
    for fn, since in expr.version_requirements():
        if since > supported:
            message = f"{fn} requires MarkLogic {since}+, service targets {version}"
            raise ValueError(message)


class _SyncExecutor:
    """Compiles an ``Expr`` and evaluates it over a synchronous eval service."""

    def __init__(
        self, rest: RestApi, version: str | MarkLogicVersion | None = None,
    ):
        self._eval = EvalService(rest)
        self._version = _coerce_version(version)

    def _evaluate(self, expr: Expr, **kwargs):
        _verify_version(expr, self._version)
        code, variables = expr.compile()
        return self._eval.xquery(code, variables=variables, **kwargs)


class _AsyncExecutor:
    """Compiles an ``Expr`` and evaluates it over an asynchronous eval service."""

    def __init__(
        self, rest: AsyncRestApi, version: str | MarkLogicVersion | None = None,
    ):
        self._eval = AsyncEvalService(rest)
        self._version = _coerce_version(version)

    async def _evaluate(self, expr: Expr, **kwargs):
        _verify_version(expr, self._version)
        code, variables = expr.compile()
        return await self._eval.xquery(code, variables=variables, **kwargs)
