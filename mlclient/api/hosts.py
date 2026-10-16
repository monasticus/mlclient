"""HostsApi / AsyncHostsApi - mid-level access to MarkLogic host endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.hosts import (
    HostGetCall,
    HostPostCall,
    HostPropertiesGetCall,
    HostPropertiesPutCall,
    HostsGetCall,
)

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class HostsApi:
    """Mid-level API for ``/manage/v2/hosts`` endpoints.

    Read hosts in the cluster, restart or shut them down, and read and update
    their properties.

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

    def get(
        self,
        host: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve information on the specified host.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/hosts/[id-or-name]

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be properties-schema,
            describe, config, counts, edit, status, or default. The edit view
            redirects (302) to the host page of the Admin Interface.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the host details

        Raises
        ------
        WrongParametersError
            If the format or the view is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostGetCall(host=host, data_format=data_format, view=view)
        return self._api.call(call, timeout=timeout)

    def post(
        self,
        host: str,
        body: dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Restart or shut down the specified host.

        The state change is not awaited: a restart reports 202 with a Location
        to compare timestamps through the Admin API.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/hosts/[id-or-name]

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        body : dict
            Form data with the 'state' property (the type of state change to
            initiate; allowed values: shutdown, restart) and the optional
            'failover' property (true to enable fast failover, false by default).
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with a restart timestamp and Location

        Raises
        ------
        WrongParametersError
            If the body has no state or an unsupported state.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostPostCall(host=host, body=body)
        return self._api.call(call, timeout=timeout)

    def get_properties(
        self,
        host: str,
        *,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve the modifiable properties of the specified host.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/hosts/[id-or-name]/properties

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be html, json or xml (default).
            This parameter overrides the Accept header if both are present.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the host properties

        Raises
        ------
        WrongParametersError
            If the format is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostPropertiesGetCall(host=host, data_format=data_format)
        return self._api.call(call, timeout=timeout)

    def put_properties(
        self,
        host: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Modify the properties of the specified host.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/hosts/[id-or-name]/properties

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        body : str | dict
            Host properties in XML or JSON format.
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
        WrongParametersError
            If the body is missing, blank or a JSON value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostPropertiesPutCall(host=host, body=body)
        return self._api.call(call, timeout=timeout)


class AsyncHostsApi:
    """Async mid-level API for ``/manage/v2/hosts`` endpoints."""

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

    async def get(
        self,
        host: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve information on the specified host.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/hosts/[id-or-name]

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be properties-schema,
            describe, config, counts, edit, status, or default. The edit view
            redirects (302) to the host page of the Admin Interface.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the host details

        Raises
        ------
        WrongParametersError
            If the format or the view is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostGetCall(host=host, data_format=data_format, view=view)
        return await self._api.call(call, timeout=timeout)

    async def post(
        self,
        host: str,
        body: dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Restart or shut down the specified host.

        The state change is not awaited: a restart reports 202 with a Location
        to compare timestamps through the Admin API.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/hosts/[id-or-name]

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        body : dict
            Form data with the 'state' property (the type of state change to
            initiate; allowed values: shutdown, restart) and the optional
            'failover' property (true to enable fast failover, false by default).
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with a restart timestamp and Location

        Raises
        ------
        WrongParametersError
            If the body has no state or an unsupported state.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostPostCall(host=host, body=body)
        return await self._api.call(call, timeout=timeout)

    async def get_properties(
        self,
        host: str,
        *,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve the modifiable properties of the specified host.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/hosts/[id-or-name]/properties

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be html, json or xml (default).
            This parameter overrides the Accept header if both are present.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the host properties

        Raises
        ------
        WrongParametersError
            If the format is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostPropertiesGetCall(host=host, data_format=data_format)
        return await self._api.call(call, timeout=timeout)

    async def put_properties(
        self,
        host: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Modify the properties of the specified host.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/hosts/[id-or-name]/properties

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        body : str | dict
            Host properties in XML or JSON format.
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
        WrongParametersError
            If the body is missing, blank or a JSON value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostPropertiesPutCall(host=host, body=body)
        return await self._api.call(call, timeout=timeout)
