"""Shared base of the services that run code on MarkLogic (eval and invoke)."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from mlclient._options import UNSET
from mlclient.responses import MLResponseParser
from mlclient.services.scope import ServiceScope

if TYPE_CHECKING:
    from httpx import Response

    from mlclient.api.rest import AsyncRestApi, RestApi
    from mlclient.models.results import ParsedValue

ScopedService = TypeVar("ScopedService", bound="ExecutionService")


class ExecutionService:
    """Base of the sync and async services that run code on MarkLogic.

    Eval and invoke send code to different endpoints, but share the database
    and transaction scope, the way external variables are combined and the
    parsing of the multipart response, which both endpoints return in the
    XDBC format. None of these perform I/O, so one base serves sync and async
    services alike.
    """

    def __init__(
        self,
        rest: RestApi | AsyncRestApi,
        scope: ServiceScope | None = None,
    ):
        """Create a service on the supplied REST connection.

        Parameters
        ----------
        rest : RestApi | AsyncRestApi
            REST transport shared by this service and its scoped copies.
        scope : ServiceScope | None, default None
            Database and transaction defaults; None uses an empty scope.
        """
        self._rest = rest
        self._scope = ServiceScope().overridden_by(scope)

    def __call__(
        self: ScopedService,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
    ) -> ScopedService:
        """Return a scoped copy without opening a connection or a transaction.

        Parameters
        ----------
        database : str | None, default unset
            Content database; unset inherits, None clears the inherited value.
        txid : str | None, default unset
            Transaction identifier; unset inherits, None clears the inherited value.

        Returns
        -------
        ScopedService
            A new service of the same class, using the same REST transport
            and the merged scope.
        """
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        return type(self)(self._rest, scope)

    def _request_scope(
        self,
        database: str | None,
        txid: str | None,
    ) -> dict:
        """Resolve one request's database and transaction against the service scope.

        Parameters
        ----------
        database : str | None
            Content database; unset inherits the service scope, None clears it.
        txid : str | None
            Transaction identifier; unset inherits the service scope, None clears it.

        Returns
        -------
        dict
            The ``database`` and ``txid`` endpoint arguments; a value that is
            unset everywhere resolves to None, selecting the server's default.
        """
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        return scope.request_params()

    @staticmethod
    def _merge_variables(
        variables: dict | None,
        kwargs: dict,
    ) -> dict:
        """Combine explicit external variables with keyword-argument variables.

        Parameters
        ----------
        variables : dict | None
            External variables passed as a dictionary; it is not modified.
        kwargs : dict
            External variables passed as keyword arguments.

        Returns
        -------
        dict
            A new dictionary; a keyword argument overrides the explicit
            variable of the same name.
        """
        return {**(variables or {}), **kwargs}

    @staticmethod
    def _parse_result(
        response: Response,
        output_type: type | None,
    ) -> ParsedValue:
        """Raise for a failed response, otherwise parse its multipart result.

        Parameters
        ----------
        response : Response
            An eval or invoke response.
        output_type : type | None
            A raw output type (``str`` or ``bytes``); None parses each item.

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        MarkLogicError
            If MarkLogic describes the failure in the response body.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        """
        MLResponseParser.raise_for_status(response)
        return MLResponseParser.parse(response, output_type=output_type)
