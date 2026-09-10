"""DatabasesApi / AsyncDatabasesApi - MarkLogic database endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import (
    DatabaseDeleteCall,
    DatabaseGetCall,
    DatabasePostCall,
    DatabasePropertiesGetCall,
    DatabasePropertiesPutCall,
    DatabasesGetCall,
    DatabasesPostCall,
)
from mlclient.connection import UNSET

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class DatabasesApi:
    """Mid-level API for ``/manage/v2/databases`` endpoints.

    Create, read, update, and delete databases in the cluster.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve a summary of the databases in the cluster.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/databases

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be schema, properties-schema, metrics, package, describe, or default.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the databases summary
        """
        call = DatabasesGetCall(data_format=data_format, view=view)
        return self._api.call(call, timeout=timeout)

    def create(
        self,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Create a new database in the cluster.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/databases

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasesPostCall(body=body)
        return self._api.call(call, timeout=timeout)

    def get(
        self,
        database: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve information on the specified database.

        The database can be identified either by ID or name.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/databases/[id-or-name]

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data.
            Can be: properties-schema, package, describe, config, counts, edit, status,
            forest-storage, or default.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the database details
        """
        call = DatabaseGetCall(database=database, data_format=data_format, view=view)
        return self._api.call(call, timeout=timeout)

    def post(
        self,
        database: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Clear or configure the specified database.

        Can be used to clear the contents of the named database and to perform
        various configuration operations on the database.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/databases/[id-or-name]

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : str | dict
            A database properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasePostCall(database=database, body=body)
        return self._api.call(call, timeout=timeout)

    def delete(
        self,
        database: str,
        *,
        forest_delete: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Delete the specified database from the cluster.

        Documentation: https://docs.marklogic.com/REST/DELETE/manage/v2/databases/[id-or-name]

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        forest_delete : str
            Specifies to delete the forests attached to the database.
            If unspecified, the forests will not be affected.
            If "configuration" is specified, the forest configuration will be removed
            but public forest data will remain.
            If "data" is specified, the forest configuration and data will be removed.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabaseDeleteCall(database=database, forest_delete=forest_delete)
        return self._api.call(call, timeout=timeout)

    def get_properties(
        self,
        database: str,
        *,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve the modifiable properties of the specified database.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/databases/[id-or-name]/properties

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the database properties
        """
        call = DatabasePropertiesGetCall(database=database, data_format=data_format)
        return self._api.call(call, timeout=timeout)

    def put_properties(
        self,
        database: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Modify the properties of the specified database.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/databases/[id-or-name]/properties

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : str | dict
            A database properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasePropertiesPutCall(database=database, body=body)
        return self._api.call(call, timeout=timeout)


class AsyncDatabasesApi:
    """Async mid-level API for ``/manage/v2/databases`` endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve a summary of the databases in the cluster."""
        call = DatabasesGetCall(data_format=data_format, view=view)
        return await self._api.call(call, timeout=timeout)

    async def create(
        self,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Create a new database in the cluster."""
        call = DatabasesPostCall(body=body)
        return await self._api.call(call, timeout=timeout)

    async def get(
        self,
        database: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve information on the specified database."""
        call = DatabaseGetCall(database=database, data_format=data_format, view=view)
        return await self._api.call(call, timeout=timeout)

    async def post(
        self,
        database: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Clear or configure the specified database."""
        call = DatabasePostCall(database=database, body=body)
        return await self._api.call(call, timeout=timeout)

    async def delete(
        self,
        database: str,
        *,
        forest_delete: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Delete the specified database from the cluster."""
        call = DatabaseDeleteCall(database=database, forest_delete=forest_delete)
        return await self._api.call(call, timeout=timeout)

    async def get_properties(
        self,
        database: str,
        *,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve the modifiable properties of the specified database."""
        call = DatabasePropertiesGetCall(database=database, data_format=data_format)
        return await self._api.call(call, timeout=timeout)

    async def put_properties(
        self,
        database: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Modify the properties of the specified database."""
        call = DatabasePropertiesPutCall(database=database, body=body)
        return await self._api.call(call, timeout=timeout)
