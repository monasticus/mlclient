"""EvalApi / AsyncEvalApi - mid-level access to MarkLogic eval endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import EvalCall

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class EvalApi:
    """Mid-level API for ``/v1/eval`` endpoint.

    Evaluate ad-hoc XQuery or server-side JavaScript queries.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def post(
        self,
        *,
        xquery: str | None = None,
        javascript: str | None = None,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
    ) -> Response:
        """Evaluate an ad-hoc query expressed using XQuery or server-side JavaScript.

        Documentation: https://docs.marklogic.com/REST/POST/v1/eval

        Parameters
        ----------
        xquery : str
            The query to evaluate, expressed using XQuery.
            You must include either this parameter or the javascript parameter,
            but not both.
        javascript : str
            The query to evaluate, expressed using server-side JavaScript.
            You must include either this parameter or the xquery parameter,
            but not both.
        variables : dict
            External variables to pass to the query during evaluation
        database : str
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str
            The transaction identifier of the multi-statement transaction
            in which to service this request.

        Returns
        -------
        Response
            An HTTP response with ``multipart/mixed`` body containing
            the evaluation results
        """
        call = EvalCall(
            xquery=xquery,
            javascript=javascript,
            variables=variables,
            database=database,
            txid=txid,
        )
        return self._api.call(call)


class AsyncEvalApi:
    """Async mid-level API for ``/v1/eval`` endpoint."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def post(
        self,
        *,
        xquery: str | None = None,
        javascript: str | None = None,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
    ) -> Response:
        """Evaluate an ad-hoc query expressed using XQuery or server-side JavaScript."""
        call = EvalCall(
            xquery=xquery,
            javascript=javascript,
            variables=variables,
            database=database,
            txid=txid,
        )
        return await self._api.call(call)
