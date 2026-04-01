"""ForestsApi / AsyncForestsApi - mid-level access to MarkLogic forest endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import (
    ForestDeleteCall,
    ForestGetCall,
    ForestPostCall,
    ForestPropertiesGetCall,
    ForestPropertiesPutCall,
    ForestsGetCall,
    ForestsPostCall,
    ForestsPutCall,
)

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class ForestsApi:
    """Mid-level API for ``/manage/v2/forests`` endpoints.

    Create, read, update, and delete forests in the cluster.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        database: str | None = None,
        group: str | None = None,
        host: str | None = None,
        full_refs: bool | None = None,
    ) -> Response:
        """Retrieve data about the forests in the cluster.

        The data returned depends on the view. If no view is specified, this
        request returns a summary of the forests in the cluster.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/forests

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be either describe, default, status, metrics, schema, storage,
            or properties-schema.
        database : str
            Returns a summary of the forests for the specified database.
            The database can be identified either by id or name.
        group : str
            Returns a summary of the forests for the specified group.
            The group can be identified either by id or name.
        host : str
            Returns a summary of the forests for the specified host.
            The host can be identified either by id or name.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first
            references.

        Returns
        -------
        Response
            An HTTP response with the forests summary
        """
        call = ForestsGetCall(
            data_format=data_format,
            view=view,
            database=database,
            group=group,
            host=host,
            full_refs=full_refs,
        )
        return self._api.call(call)

    def create(
        self,
        body: str | dict,
        *,
        wait_for_forest_to_mount: bool | None = None,
    ) -> Response:
        """Create a new forest, including replicas if specified.

        If a database id or database is included, attach the new forest(s)
        to the database.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/forests

        Parameters
        ----------
        body : str | dict
            A forest properties in XML or JSON format.
        wait_for_forest_to_mount : bool
            Whether to wait for the new forest to mount before sending a response
            to this request. Allowed values: true (default) or false.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestsPostCall(
            body=body,
            wait_for_forest_to_mount=wait_for_forest_to_mount,
        )
        return self._api.call(call)

    def put(
        self,
        body: str | dict,
    ) -> Response:
        """Perform an operation on one or more forests.

        Such as combining multiple forests into a single new one, or migrating
        the data in the forests to a new data directory.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/forests

        Parameters
        ----------
        body : str | dict
            A forest properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestsPutCall(body=body)
        return self._api.call(call)

    def get(
        self,
        forest: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve information about a forest.

        The forest can be identified either by ID or name.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/forests/[id-or-name]

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be properties-schema, config, edit, package, describe, status,
            xdmp:server-status or default.

        Returns
        -------
        Response
            An HTTP response with the forest details
        """
        call = ForestGetCall(forest=forest, data_format=data_format, view=view)
        return self._api.call(call)

    def post(
        self,
        forest: str,
        body: str | dict,
    ) -> Response:
        """Initiate a state change on a forest, such as a merge, restart, or attach.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/forests/[id-or-name]

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        body : dict
            A list of properties. Need to include the 'state' property (the type
            of state change to initiate).
            Allowed values: clear, merge, restart, attach, detach, retire, employ.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestPostCall(forest=forest, body=body)
        return self._api.call(call)

    def delete(
        self,
        forest: str,
        *,
        level: str,
        replicas: str | None = None,
    ) -> Response:
        """Delete a forest.

        Documentation: https://docs.marklogic.com/REST/DELETE/manage/v2/forests/[id-or-name]

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        level : str
            The type of state change to initiate. Allowed values: full, config-only.
            A config-only deletion removes only the forest configuration;
            the data contained in the forest remains on disk.
            A full deletion removes both the forest configuration and the data.
        replicas : str
            Determines how to process the replicas.
            Allowed values: detach to detach the replica but keep it; delete to detach
            and delete the replica.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestDeleteCall(forest=forest, level=level, replicas=replicas)
        return self._api.call(call)

    def get_properties(
        self,
        forest: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Retrieve the modifiable properties of a forest.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/forests/[id-or-name]/properties

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            An HTTP response with the forest properties
        """
        call = ForestPropertiesGetCall(forest=forest, data_format=data_format)
        return self._api.call(call)

    def put_properties(
        self,
        forest: str,
        body: str | dict,
    ) -> Response:
        """Modify the configuration of a forest.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/forests/[id-or-name]/properties

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        body : str | dict
            A forest properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestPropertiesPutCall(forest=forest, body=body)
        return self._api.call(call)


class AsyncForestsApi:
    """Async mid-level API for ``/manage/v2/forests`` endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        database: str | None = None,
        group: str | None = None,
        host: str | None = None,
        full_refs: bool | None = None,
    ) -> Response:
        """Retrieve data about the forests in the cluster."""
        call = ForestsGetCall(
            data_format=data_format,
            view=view,
            database=database,
            group=group,
            host=host,
            full_refs=full_refs,
        )
        return await self._api.call(call)

    async def create(
        self,
        body: str | dict,
        *,
        wait_for_forest_to_mount: bool | None = None,
    ) -> Response:
        """Create a new forest, including replicas if specified."""
        call = ForestsPostCall(
            body=body,
            wait_for_forest_to_mount=wait_for_forest_to_mount,
        )
        return await self._api.call(call)

    async def put(
        self,
        body: str | dict,
    ) -> Response:
        """Perform an operation on one or more forests."""
        call = ForestsPutCall(body=body)
        return await self._api.call(call)

    async def get(
        self,
        forest: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve information about a forest."""
        call = ForestGetCall(forest=forest, data_format=data_format, view=view)
        return await self._api.call(call)

    async def post(
        self,
        forest: str,
        body: str | dict,
    ) -> Response:
        """Initiate a state change on a forest, such as a merge, restart, or attach."""
        call = ForestPostCall(forest=forest, body=body)
        return await self._api.call(call)

    async def delete(
        self,
        forest: str,
        *,
        level: str,
        replicas: str | None = None,
    ) -> Response:
        """Delete a forest."""
        call = ForestDeleteCall(forest=forest, level=level, replicas=replicas)
        return await self._api.call(call)

    async def get_properties(
        self,
        forest: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Retrieve the modifiable properties of a forest."""
        call = ForestPropertiesGetCall(forest=forest, data_format=data_format)
        return await self._api.call(call)

    async def put_properties(
        self,
        forest: str,
        body: str | dict,
    ) -> Response:
        """Modify the configuration of a forest."""
        call = ForestPropertiesPutCall(forest=forest, body=body)
        return await self._api.call(call)
