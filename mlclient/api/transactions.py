"""TransactionsApi / AsyncTransactionsApi - MarkLogic transaction endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import TransactionGetCall, TransactionPostCall, TransactionsPostCall

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class TransactionsApi:
    """Mid-level API for ``/v1/transactions`` endpoints.

    Create, inspect, and commit or roll back multi-statement transactions.

    Requires a REST app server.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def create(
        self,
        *,
        name: str | None = None,
        time_limit: int | None = None,
        database: str | None = None,
    ) -> Response:
        """Create a multi-statement transaction.

        The response is a 303 redirect whose ``Location`` header carries the new
        transaction id (``/v1/transactions/{txid}``); the redirect is not followed.

        Documentation: https://docs.marklogic.com/REST/POST/v1/transactions

        Parameters
        ----------
        name : str
            A name to assign to the transaction.
        time_limit : int
            The maximum number of seconds for the transaction to remain open.
        database : str
            Evaluate against the named content database instead of the default
            content database associated with the REST API instance.

        Returns
        -------
        Response
            An HTTP response with a ``Location`` header carrying the transaction id
        """
        call = TransactionsPostCall(
            name=name,
            time_limit=time_limit,
            database=database,
        )
        return self._api.call(call)

    def get(
        self,
        txid: str,
        *,
        data_format: str | None = None,
        database: str | None = None,
    ) -> Response:
        """Retrieve the status of the specified transaction.

        Documentation: https://docs.marklogic.com/REST/GET/v1/transactions/[txid]

        Parameters
        ----------
        txid : str
            A transaction identifier.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
        database : str
            Evaluate against the named content database instead of the default
            content database associated with the REST API instance.

        Returns
        -------
        Response
            An HTTP response with the transaction status
        """
        call = TransactionGetCall(
            txid=txid,
            data_format=data_format,
            database=database,
        )
        return self._api.call(call)

    def post(
        self,
        txid: str,
        *,
        result: str,
        database: str | None = None,
    ) -> Response:
        """Commit or roll back the specified transaction.

        Documentation: https://docs.marklogic.com/REST/POST/v1/transactions/[txid]

        Parameters
        ----------
        txid : str
            A transaction identifier.
        result : str
            The disposition of the transaction. Can be either commit or rollback.
        database : str
            Evaluate against the named content database instead of the default
            content database associated with the REST API instance.

        Returns
        -------
        Response
            An HTTP response
        """
        call = TransactionPostCall(
            txid=txid,
            result=result,
            database=database,
        )
        return self._api.call(call)


class AsyncTransactionsApi:
    """Async mid-level API for ``/v1/transactions`` endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def create(
        self,
        *,
        name: str | None = None,
        time_limit: int | None = None,
        database: str | None = None,
    ) -> Response:
        """Create a multi-statement transaction."""
        call = TransactionsPostCall(
            name=name,
            time_limit=time_limit,
            database=database,
        )
        return await self._api.call(call)

    async def get(
        self,
        txid: str,
        *,
        data_format: str | None = None,
        database: str | None = None,
    ) -> Response:
        """Retrieve the status of the specified transaction."""
        call = TransactionGetCall(
            txid=txid,
            data_format=data_format,
            database=database,
        )
        return await self._api.call(call)

    async def post(
        self,
        txid: str,
        *,
        result: str,
        database: str | None = None,
    ) -> Response:
        """Commit or roll back the specified transaction."""
        call = TransactionPostCall(
            txid=txid,
            result=result,
            database=database,
        )
        return await self._api.call(call)
