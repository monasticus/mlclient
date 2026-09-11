"""GroupsApi / AsyncGroupsApi - mid-level access to MarkLogic group endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import GroupPropertiesGetCall, GroupPropertiesPutCall
from mlclient.connection import UNSET

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class GroupsApi:
    """Mid-level API for ``/manage/v2/groups`` endpoints.

    Read and update the properties of a group in the cluster.

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
