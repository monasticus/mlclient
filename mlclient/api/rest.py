"""REST API group for /v1/* endpoints (RestApi / AsyncRestApi).

Requires a REST app server.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.base import ApiCall

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient

from mlclient.api.documents import AsyncDocumentsApi, DocumentsApi
from mlclient.api.eval import AsyncEvalApi, EvalApi
from mlclient.api.transactions import AsyncTransactionsApi, TransactionsApi


class RestApi:
    """REST API group for /v1/* endpoints (eval, documents, transactions).

    Requires a REST app server.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return self._api.call(call_, timeout=timeout)

    @cached_property
    def eval(self) -> EvalApi:
        """Access eval operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        EvalApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return EvalApi(self._api)

    @cached_property
    def documents(self) -> DocumentsApi:
        """Access documents operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        DocumentsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return DocumentsApi(self._api)

    @cached_property
    def transactions(self) -> TransactionsApi:
        """Access transactions operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        TransactionsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return TransactionsApi(self._api)


class AsyncRestApi:
    """Async REST API group for /v1/* endpoints (eval, documents, transactions)."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return await self._api.call(call_, timeout=timeout)

    @cached_property
    def eval(self) -> AsyncEvalApi:
        """Access eval operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncEvalApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncEvalApi(self._api)

    @cached_property
    def documents(self) -> AsyncDocumentsApi:
        """Access documents operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncDocumentsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncDocumentsApi(self._api)

    @cached_property
    def transactions(self) -> AsyncTransactionsApi:
        """Access transactions operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncTransactionsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncTransactionsApi(self._api)
