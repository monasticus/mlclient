"""EvalApi - mid-level access to MarkLogic eval endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import EvalCall

if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class EvalApi:
    """Mid-level API for /v1/eval endpoint."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def post(
        self,
        xquery: str | None = None,
        javascript: str | None = None,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
    ) -> Response:
        """Send a POST request to the /v1/eval endpoint."""
        call = EvalCall(
            xquery=xquery,
            javascript=javascript,
            variables=variables,
            database=database,
            txid=txid,
        )
        return self._rest.call(call)
