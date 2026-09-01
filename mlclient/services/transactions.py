"""Per-transaction service (TransactionService / AsyncTransactionService).

Each instance is scoped to a single open multi-statement transaction and only
ever calls the ``/v1/transactions/{txid}`` endpoints. Opening a transaction
(``POST /v1/transactions``) is the client's responsibility, exposed through
``MLClient.transaction(...)`` / ``AsyncMLClient.transaction(...)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from mlclient.api.transactions import AsyncTransactionsApi, TransactionsApi
from mlclient.exceptions import MarkLogicError
from mlclient.ml_response_parser import MLResponseParser

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import TracebackType

    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class TransactionService:
    """A single open multi-statement transaction on MarkLogic.

    Acts as a context manager: commits on a clean exit, rolls back if the block
    raises. Unpacks (``**``) into ``txid`` and ``database`` keyword arguments so
    it can be spread into content operations (eval, documents) that must run
    within the transaction and against the same database it was opened on.
    """

    def __init__(self, api: TransactionsApi, txid: str, database: str | None = None):
        self._api = api
        self._txid = txid
        self._database = database

    @property
    def id(self) -> str:
        """The server-assigned transaction id."""
        return self._txid

    @property
    def database(self) -> str | None:
        """The content database the transaction was opened against."""
        return self._database

    def __enter__(self) -> TransactionService:
        """Return the open transaction for use in a ``with`` block."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Commit on a clean exit; roll back if the block raised."""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    def status(self, *, data_format: str = "json"):
        """Return the status of the transaction.

        Parameters
        ----------
        data_format : str, default "json"
            The format of the returned status; either json or xml

        Returns
        -------
        The parsed transaction status

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        resp = self._api.get(
            self._txid,
            data_format=data_format,
            database=self._database,
        )
        parsed_resp = MLResponseParser.parse(resp)
        if not resp.is_success:
            raise MarkLogicError(parsed_resp["errorResponse"])
        return parsed_resp

    def commit(self) -> None:
        """Commit the transaction.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        self._finish("commit")

    def rollback(self) -> None:
        """Roll back the transaction.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        self._finish("rollback")

    def _finish(self, result: str) -> None:
        resp = self._api.post(self._txid, result=result, database=self._database)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])

    def keys(self) -> Iterable[str]:
        """Return the keys exposed for ``**`` unpacking (txid, database if set)."""
        if self._database is None:
            return ("txid",)
        return ("txid", "database")

    def __getitem__(self, key: str):
        """Return the value for a ``**``-unpacking key (txid or database)."""
        if key == "txid":
            return self._txid
        if key == "database":
            return self._database
        raise KeyError(key)


def open_transaction(
    api: ApiClient,
    *,
    name: str | None = None,
    time_limit: int | None = None,
    database: str | None = None,
) -> TransactionService:
    """Open a multi-statement transaction and return a service scoped to it.

    Parameters
    ----------
    api : ApiClient
        The client used both to open the transaction and by the returned service
    name : str | None, default None
        A name to assign to the transaction
    time_limit : int | None, default None
        The maximum number of seconds for the transaction to remain open
    database : str | None, default None
        Content database name or id to open the transaction against

    Returns
    -------
    TransactionService
        A service scoped to the newly opened transaction

    Raises
    ------
    MarkLogicError
        If MarkLogic returns an error
    """
    transactions = TransactionsApi(api)
    resp = transactions.create(name=name, time_limit=time_limit, database=database)
    txid = _txid_or_raise(resp)
    return TransactionService(transactions, txid, database)


class AsyncTransactionService:
    """Async per-transaction service; see TransactionService."""

    def __init__(
        self,
        api: AsyncTransactionsApi,
        txid: str,
        database: str | None = None,
    ):
        self._api = api
        self._txid = txid
        self._database = database

    @property
    def id(self) -> str:
        """The server-assigned transaction id."""
        return self._txid

    @property
    def database(self) -> str | None:
        """The content database the transaction was opened against."""
        return self._database

    async def __aenter__(self) -> AsyncTransactionService:
        """Return the open transaction for use in an ``async with`` block."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Commit on a clean exit; roll back if the block raised."""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def status(self, *, data_format: str = "json"):
        """Return the status of the transaction."""
        resp = await self._api.get(
            self._txid,
            data_format=data_format,
            database=self._database,
        )
        parsed_resp = MLResponseParser.parse(resp)
        if not resp.is_success:
            raise MarkLogicError(parsed_resp["errorResponse"])
        return parsed_resp

    async def commit(self) -> None:
        """Commit the transaction."""
        await self._finish("commit")

    async def rollback(self) -> None:
        """Roll back the transaction."""
        await self._finish("rollback")

    async def _finish(self, result: str) -> None:
        resp = await self._api.post(
            self._txid,
            result=result,
            database=self._database,
        )
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])

    def keys(self) -> Iterable[str]:
        """Return the keys exposed for ``**`` unpacking (txid, database if set)."""
        if self._database is None:
            return ("txid",)
        return ("txid", "database")

    def __getitem__(self, key: str):
        """Return the value for a ``**``-unpacking key (txid or database)."""
        if key == "txid":
            return self._txid
        if key == "database":
            return self._database
        raise KeyError(key)


async def async_open_transaction(
    api: AsyncApiClient,
    *,
    name: str | None = None,
    time_limit: int | None = None,
    database: str | None = None,
) -> AsyncTransactionService:
    """Open a multi-statement transaction and return a service scoped to it."""
    transactions = AsyncTransactionsApi(api)
    resp = await transactions.create(
        name=name,
        time_limit=time_limit,
        database=database,
    )
    txid = _txid_or_raise(resp)
    return AsyncTransactionService(transactions, txid, database)


def _txid_or_raise(resp: httpx.Response) -> str:
    if resp.status_code != httpx.codes.SEE_OTHER:
        resp_body = MLResponseParser.parse(resp)
        raise MarkLogicError(resp_body["errorResponse"])
    return resp.headers["Location"].rsplit("/", 1)[-1]
