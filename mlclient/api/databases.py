"""DatabasesApi - mid-level access to MarkLogic database endpoints."""

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

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient


class DatabasesApi:
    """Mid-level API for ``/manage/v2/databases`` endpoints.

    Create, read, update, and delete databases in the cluster.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, client: ApiClient):
        self._client = client

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
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

        Returns
        -------
        Response
            An HTTP response with the databases summary
        """
        call = DatabasesGetCall(data_format=data_format, view=view)
        return self._client.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Create a new database in the cluster.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/databases

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasesPostCall(body=body)
        return self._client.call(call)

    def get(
        self,
        database: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
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

        Returns
        -------
        Response
            An HTTP response with the database details
        """
        call = DatabaseGetCall(database=database, data_format=data_format, view=view)
        return self._client.call(call)

    def post(
        self,
        database: str,
        body: str | dict,
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

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasePostCall(database=database, body=body)
        return self._client.call(call)

    def delete(
        self,
        database: str,
        *,
        forest_delete: str | None = None,
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

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabaseDeleteCall(database=database, forest_delete=forest_delete)
        return self._client.call(call)

    def get_properties(
        self,
        database: str,
        *,
        data_format: str | None = None,
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

        Returns
        -------
        Response
            An HTTP response with the database properties
        """
        call = DatabasePropertiesGetCall(database=database, data_format=data_format)
        return self._client.call(call)

    def put_properties(
        self,
        database: str,
        body: str | dict,
    ) -> Response:
        """Modify the properties of the specified database.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/databases/[id-or-name]/properties

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : str | dict
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasePropertiesPutCall(database=database, body=body)
        return self._client.call(call)
