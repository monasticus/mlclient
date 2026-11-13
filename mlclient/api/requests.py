"""RequestsApi / AsyncRequestsApi - mid-level access to MarkLogic request endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.requests import RequestGetCall, RequestsGetCall

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class RequestsApi:
    """Mid-level API for ``/manage/v2/requests`` endpoints.

    Read the requests running in the cluster. The resource is read-only.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, api: ApiClient):
        """Bind request operations to a synchronous API client.

        Parameters
        ----------
        api : ApiClient
            The transport used to send requests.
        """
        self._api = api

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        group_id: str | None = None,
        host_id: str | None = None,
        server_id: str | None = None,
        seconds_min: int | None = None,
        full_refs: bool | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve a summary of the requests running in the cluster.

        Each listed request carries its id (``idref``), elapsed seconds,
        request kind and text, and whether it is an update. Use seconds_min
        to see what still runs, e.g. after a client-side timeout. MarkLogic
        offers no REST endpoint to cancel a request.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/requests

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be default, schema or describe.
            The schema view requires XML format.
        group_id : str
            Limits the summary to requests in the specified group.
            The group can be identified either by id or name.
        host_id : str
            Limits the summary to requests in the specified host.
            The host can be identified either by id or name.
        server_id : str
            Limits the summary to requests in the specified server.
            The server can be identified either by id or name;
            a name requires group_id.
        seconds_min : int
            Returns only requests that have been executing for at least
            the specified whole number of seconds.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first
            references.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the requests summary

        Raises
        ------
        WrongParametersError
            If the format or view is unsupported, or seconds_min is not
            a non-negative integer.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = RequestsGetCall(
            data_format=data_format,
            view=view,
            group_id=group_id,
            host_id=host_id,
            server_id=server_id,
            seconds_min=seconds_min,
            full_refs=full_refs,
        )
        return self._api.call(call, timeout=timeout)

    def get(
        self,
        request: str,
        *,
        data_format: str | None = None,
        group_id: str | None = None,
        host_id: str | None = None,
        server_id: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve information on the specified request.

        MarkLogic answers 200 for an id that is not running (any more):
        the response then has no properties (null in JSON).

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/requests/[id-or-uri]

        Parameters
        ----------
        request : str
            A request identifier. The request can be identified either by id or URI.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        group_id : str
            Limits the information to the request in the specified group.
            The group can be identified either by id or name.
        host_id : str
            Limits the information to the request in the specified host.
            The host can be identified either by id or name.
        server_id : str
            Limits the information to the request in the specified server.
            The server can be identified either by id or name;
            a name requires group_id.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the request details

        Raises
        ------
        WrongParametersError
            If the format is unsupported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = RequestGetCall(
            request=request,
            data_format=data_format,
            group_id=group_id,
            host_id=host_id,
            server_id=server_id,
        )
        return self._api.call(call, timeout=timeout)


class AsyncRequestsApi:
    """Async mid-level API for ``/manage/v2/requests`` endpoints."""

    def __init__(self, api: AsyncApiClient):
        """Bind request operations to an asynchronous API client.

        Parameters
        ----------
        api : AsyncApiClient
            The transport used to send requests.
        """
        self._api = api

    async def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        group_id: str | None = None,
        host_id: str | None = None,
        server_id: str | None = None,
        seconds_min: int | None = None,
        full_refs: bool | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve a summary of the requests running in the cluster.

        Each listed request carries its id (``idref``), elapsed seconds,
        request kind and text, and whether it is an update. Use seconds_min
        to see what still runs, e.g. after a client-side timeout. MarkLogic
        offers no REST endpoint to cancel a request.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/requests

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be default, schema or describe.
            The schema view requires XML format.
        group_id : str
            Limits the summary to requests in the specified group.
            The group can be identified either by id or name.
        host_id : str
            Limits the summary to requests in the specified host.
            The host can be identified either by id or name.
        server_id : str
            Limits the summary to requests in the specified server.
            The server can be identified either by id or name;
            a name requires group_id.
        seconds_min : int
            Returns only requests that have been executing for at least
            the specified whole number of seconds.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first
            references.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the requests summary

        Raises
        ------
        WrongParametersError
            If the format or view is unsupported, or seconds_min is not
            a non-negative integer.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = RequestsGetCall(
            data_format=data_format,
            view=view,
            group_id=group_id,
            host_id=host_id,
            server_id=server_id,
            seconds_min=seconds_min,
            full_refs=full_refs,
        )
        return await self._api.call(call, timeout=timeout)

    async def get(
        self,
        request: str,
        *,
        data_format: str | None = None,
        group_id: str | None = None,
        host_id: str | None = None,
        server_id: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve information on the specified request.

        MarkLogic answers 200 for an id that is not running (any more):
        the response then has no properties (null in JSON).

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/requests/[id-or-uri]

        Parameters
        ----------
        request : str
            A request identifier. The request can be identified either by id or URI.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        group_id : str
            Limits the information to the request in the specified group.
            The group can be identified either by id or name.
        host_id : str
            Limits the information to the request in the specified host.
            The host can be identified either by id or name.
        server_id : str
            Limits the information to the request in the specified server.
            The server can be identified either by id or name;
            a name requires group_id.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the request details

        Raises
        ------
        WrongParametersError
            If the format is unsupported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = RequestGetCall(
            request=request,
            data_format=data_format,
            group_id=group_id,
            host_id=host_id,
            server_id=server_id,
        )
        return await self._api.call(call, timeout=timeout)
