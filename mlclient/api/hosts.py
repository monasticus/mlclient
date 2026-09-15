"""HostsApi / AsyncHostsApi - mid-level access to MarkLogic hosts endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.hosts import HostsGetCall

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class HostsApi:
    """Mid-level API for ``/manage/v2/hosts`` endpoint.

    Retrieve information about the hosts in the cluster.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, api: ApiClient):
        """Bind host operations to a synchronous API client.

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
        group_id: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve data about the hosts in the cluster.

        The data returned depends on the setting of the view request parameter.
        The default view provides a summary of the hosts.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/hosts

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        group_id : str
            Specifies to return only the hosts in the specified group.
            The group can be identified either by id or name.
            If not specified, the response includes information about all hosts.
        view : str
            A specific view of the returned data.
            Can be default, status, metrics, schema, properties-schema, or describe.
            The schema view requires XML format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the hosts summary

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostsGetCall(data_format=data_format, group_id=group_id, view=view)
        return self._api.call(call, timeout=timeout)


class AsyncHostsApi:
    """Async mid-level API for ``/manage/v2/hosts`` endpoint."""

    def __init__(self, api: AsyncApiClient):
        """Bind host operations to an asynchronous API client.

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
        group_id: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve data about the hosts in the cluster.

        The data returned depends on the setting of the view request parameter.
        The default view provides a summary of the hosts.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/hosts

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        group_id : str
            Specifies to return only the hosts in the specified group.
            The group can be identified either by id or name.
            If not specified, the response includes information about all hosts.
        view : str
            A specific view of the returned data.
            Can be default, status, metrics, schema, properties-schema, or describe.
            The schema view requires XML format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the hosts summary

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostsGetCall(data_format=data_format, group_id=group_id, view=view)
        return await self._api.call(call, timeout=timeout)
