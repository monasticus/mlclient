"""GroupsApi / AsyncGroupsApi - mid-level access to MarkLogic group endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.groups import (
    GroupDeleteCall,
    GroupGetCall,
    GroupPostCall,
    GroupPropertiesGetCall,
    GroupPropertiesPutCall,
    GroupsGetCall,
    GroupsPostCall,
)

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class GroupsApi:
    """Mid-level API for ``/manage/v2/groups`` endpoints.

    Create, read, update, restart, shut down and delete groups in the cluster.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, api: ApiClient):
        """Initialize the group API.

        Parameters
        ----------
        api : ApiClient
            Client connected to the Management server
        """
        self._api = api

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve a summary of the groups in the cluster.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/groups

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be schema, describe,
            or default. The schema view requires XML format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the groups summary

        Raises
        ------
        WrongParametersError
            If the format or the view is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = GroupsGetCall(data_format=data_format, view=view)
        return self._api.call(call, timeout=timeout)

    def create(
        self,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Create a new group in the cluster.

        A group that already exists is not changed and is reported as created
        too (201), without a Location header.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/groups

        Parameters
        ----------
        body : str | dict
            Group properties in XML or JSON format. The group-name property
            is required.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 201 with the Location of a new group

        Raises
        ------
        WrongParametersError
            If the body is missing, blank or a JSON value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = GroupsPostCall(body=body)
        return self._api.call(call, timeout=timeout)

    def get(
        self,
        group: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve information on the specified group.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/groups/[id-or-name]

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be properties-schema,
            describe, config, counts, edit, status, or default. The edit view
            redirects (302) to the group page of the Admin Interface.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the group details

        Raises
        ------
        WrongParametersError
            If the format or the view is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = GroupGetCall(group=group, data_format=data_format, view=view)
        return self._api.call(call, timeout=timeout)

    def post(
        self,
        group: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Restart or shut down a group.

        Both operations restart or stop every host in the group; MarkLogic
        rejects them (400) when the group has no hosts.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/groups/[id-or-name]

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        body : str | dict
            The operation in XML or JSON format: {"operation": "restart-group"}
            or {"operation": "shutdown-group"}.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with the restart timestamp in the body

        Raises
        ------
        WrongParametersError
            If the body is missing, blank or a JSON value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = GroupPostCall(group=group, body=body)
        return self._api.call(call, timeout=timeout)

    def delete(
        self,
        group: str,
        *,
        timeout=UNSET,
    ) -> Response:
        """Delete the specified group from the cluster.

        Deleting a group that does not exist also succeeds (204).

        Documentation: https://docs.marklogic.com/REST/DELETE/manage/v2/groups/[id-or-name]

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
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
        call = GroupDeleteCall(group=group)
        return self._api.call(call, timeout=timeout)

    def get_properties(
        self,
        group: str,
        *,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve the modifiable properties of the specified group.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/groups/[id-or-name]/properties

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter overrides the Accept header if both are present.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset uses the client configuration;
            None disables it; a number sets all four components; an
            httpx.Timeout sets them independently. Not sent as a query parameter.

        Returns
        -------
        Response
            An HTTP response with the group properties

        Raises
        ------
        httpx.TimeoutException
            If an HTTP timeout expires after any configured retries
        """
        call = GroupPropertiesGetCall(group=group, data_format=data_format)
        return self._api.call(call, timeout=timeout)

    def put_properties(
        self,
        group: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Modify the properties of the specified group.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/groups/[id-or-name]/properties

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        body : str | dict
            Group properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset uses the client configuration;
            None disables it; a number sets all four components; an
            httpx.Timeout sets them independently. Not sent as a query parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP timeout expires after any configured retries
        """
        call = GroupPropertiesPutCall(group=group, body=body)
        return self._api.call(call, timeout=timeout)


class AsyncGroupsApi:
    """Async mid-level API for ``/manage/v2/groups`` endpoints."""

    def __init__(self, api: AsyncApiClient):
        """Initialize the asynchronous group API.

        Parameters
        ----------
        api : AsyncApiClient
            Client connected to the Management server
        """
        self._api = api

    async def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve a summary of the groups in the cluster.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/groups

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be schema, describe,
            or default. The schema view requires XML format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the groups summary

        Raises
        ------
        WrongParametersError
            If the format or the view is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = GroupsGetCall(data_format=data_format, view=view)
        return await self._api.call(call, timeout=timeout)

    async def create(
        self,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Create a new group in the cluster.

        A group that already exists is not changed and is reported as created
        too (201), without a Location header.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/groups

        Parameters
        ----------
        body : str | dict
            Group properties in XML or JSON format. The group-name property
            is required.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 201 with the Location of a new group

        Raises
        ------
        WrongParametersError
            If the body is missing, blank or a JSON value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = GroupsPostCall(body=body)
        return await self._api.call(call, timeout=timeout)

    async def get(
        self,
        group: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve information on the specified group.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/groups/[id-or-name]

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be properties-schema,
            describe, config, counts, edit, status, or default. The edit view
            redirects (302) to the group page of the Admin Interface.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the group details

        Raises
        ------
        WrongParametersError
            If the format or the view is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = GroupGetCall(group=group, data_format=data_format, view=view)
        return await self._api.call(call, timeout=timeout)

    async def post(
        self,
        group: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Restart or shut down a group.

        Both operations restart or stop every host in the group; MarkLogic
        rejects them (400) when the group has no hosts.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/groups/[id-or-name]

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        body : str | dict
            The operation in XML or JSON format: {"operation": "restart-group"}
            or {"operation": "shutdown-group"}.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with the restart timestamp in the body

        Raises
        ------
        WrongParametersError
            If the body is missing, blank or a JSON value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = GroupPostCall(group=group, body=body)
        return await self._api.call(call, timeout=timeout)

    async def delete(
        self,
        group: str,
        *,
        timeout=UNSET,
    ) -> Response:
        """Delete the specified group from the cluster.

        Deleting a group that does not exist also succeeds (204).

        Documentation: https://docs.marklogic.com/REST/DELETE/manage/v2/groups/[id-or-name]

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
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
        call = GroupDeleteCall(group=group)
        return await self._api.call(call, timeout=timeout)

    async def get_properties(
        self,
        group: str,
        *,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve the modifiable properties of the specified group.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/groups/[id-or-name]/properties

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter overrides the Accept header if both are present.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset uses the client configuration;
            None disables it; a number sets all four components; an
            httpx.Timeout sets them independently. Not sent as a query parameter.

        Returns
        -------
        Response
            An HTTP response with the group properties

        Raises
        ------
        httpx.TimeoutException
            If an HTTP timeout expires after any configured retries
        """
        call = GroupPropertiesGetCall(group=group, data_format=data_format)
        return await self._api.call(call, timeout=timeout)

    async def put_properties(
        self,
        group: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Modify the properties of the specified group.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/groups/[id-or-name]/properties

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        body : str | dict
            Group properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset uses the client configuration;
            None disables it; a number sets all four components; an
            httpx.Timeout sets them independently. Not sent as a query parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP timeout expires after any configured retries
        """
        call = GroupPropertiesPutCall(group=group, body=body)
        return await self._api.call(call, timeout=timeout)
