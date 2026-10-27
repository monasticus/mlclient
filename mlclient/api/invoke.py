"""InvokeApi / AsyncInvokeApi - mid-level access to MarkLogic invoke endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.invoke import InvokeCall

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class InvokeApi:
    """Mid-level API for ``/v1/invoke`` endpoint.

    Evaluate XQuery or server-side JavaScript modules installed in MarkLogic.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def post(
        self,
        module: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Evaluate an XQuery or server-side JavaScript module installed in MarkLogic.

        Documentation: https://docs.marklogic.com/REST/POST/v1/invoke

        Parameters
        ----------
        module : str
            The path of the module to be evaluated, resolved against the root
            of the App Server receiving the request. The module filename suffix
            determines whether the module is treated as XQuery or JavaScript.
        variables : dict
            External variables to pass to the module
        database : str
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``multipart/mixed`` body containing
            the module's results

        Raises
        ------
        WrongParametersError
            If the module path is missing or blank.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = InvokeCall(
            module=module,
            variables=variables,
            database=database,
            txid=txid,
        )
        return self._api.call(call, timeout=timeout)


class AsyncInvokeApi:
    """Async mid-level API for ``/v1/invoke`` endpoint."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def post(
        self,
        module: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Evaluate an XQuery or server-side JavaScript module installed in MarkLogic.

        Documentation: https://docs.marklogic.com/REST/POST/v1/invoke

        Parameters
        ----------
        module : str
            The path of the module to be evaluated, resolved against the root
            of the App Server receiving the request. The module filename suffix
            determines whether the module is treated as XQuery or JavaScript.
        variables : dict
            External variables to pass to the module
        database : str
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``multipart/mixed`` body containing
            the module's results

        Raises
        ------
        WrongParametersError
            If the module path is missing or blank.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = InvokeCall(
            module=module,
            variables=variables,
            database=database,
            txid=txid,
        )
        return await self._api.call(call, timeout=timeout)
