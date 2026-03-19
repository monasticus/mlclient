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

# Avoid circular import: RestClient -> api classes -> RestClient
if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class DatabasesApi:
    """Mid-level API for /manage/v2/databases endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/databases endpoint.

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
            An HTTP response
        """
        call = DatabasesGetCall(data_format=data_format, view=view)
        return self._rest.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/databases endpoint.

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
        return self._rest.call(call)

    def get(
        self,
        database: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/databases/{id|name} endpoint.

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
            An HTTP response
        """
        call = DatabaseGetCall(database=database, data_format=data_format, view=view)
        return self._rest.call(call)

    def post(
        self,
        database: str,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/databases/{id|name} endpoint.

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
        return self._rest.call(call)

    def delete(
        self,
        database: str,
        *,
        forest_delete: str | None = None,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/databases/{id|name} endpoint.

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
        return self._rest.call(call)

    def get_properties(
        self,
        database: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/databases/{id|name}/properties.

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
            An HTTP response
        """
        call = DatabasePropertiesGetCall(database=database, data_format=data_format)
        return self._rest.call(call)

    def put_properties(
        self,
        database: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/databases/{id|name}/properties.

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
        return self._rest.call(call)
