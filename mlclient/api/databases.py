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

if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class DatabasesApi:
    """Mid-level API for /manage/v2/databases endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get_list(
        self,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/databases endpoint."""
        call = DatabasesGetCall(data_format=data_format, view=view)
        return self._rest.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/databases endpoint."""
        call = DatabasesPostCall(body=body)
        return self._rest.call(call)

    def get(
        self,
        database: str,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/databases/{id|name} endpoint."""
        call = DatabaseGetCall(database=database, data_format=data_format, view=view)
        return self._rest.call(call)

    def post(
        self,
        database: str,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/databases/{id|name} endpoint."""
        call = DatabasePostCall(database=database, body=body)
        return self._rest.call(call)

    def delete(
        self,
        database: str,
        forest_delete: str | None = None,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/databases/{id|name} endpoint."""
        call = DatabaseDeleteCall(database=database, forest_delete=forest_delete)
        return self._rest.call(call)

    def get_properties(
        self,
        database: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/databases/{id|name}/properties."""
        call = DatabasePropertiesGetCall(database=database, data_format=data_format)
        return self._rest.call(call)

    def put_properties(
        self,
        database: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/databases/{id|name}/properties."""
        call = DatabasePropertiesPutCall(database=database, body=body)
        return self._rest.call(call)
