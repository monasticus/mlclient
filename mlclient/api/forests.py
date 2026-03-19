"""ForestsApi - mid-level access to MarkLogic forest endpoints."""

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

if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class ForestsApi:
    """Mid-level API for /manage/v2/forests endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get_list(
        self,
        data_format: str | None = None,
        view: str | None = None,
        database: str | None = None,
        group: str | None = None,
        host: str | None = None,
        full_refs: bool | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/forests endpoint."""
        call = ForestsGetCall(
            data_format=data_format,
            view=view,
            database=database,
            group=group,
            host=host,
            full_refs=full_refs,
        )
        return self._rest.call(call)

    def create(
        self,
        body: str | dict,
        wait_for_forest_to_mount: bool | None = None,
    ) -> Response:
        """Send a POST request to the /manage/v2/forests endpoint."""
        call = ForestsPostCall(
            body=body,
            wait_for_forest_to_mount=wait_for_forest_to_mount,
        )
        return self._rest.call(call)

    def put(
        self,
        body: str | dict,
    ) -> Response:
        """Send a PUT request to the /manage/v2/forests endpoint."""
        call = ForestsPutCall(body=body)
        return self._rest.call(call)

    def get(
        self,
        forest: str,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/forests/{id|name} endpoint."""
        call = ForestGetCall(forest=forest, data_format=data_format, view=view)
        return self._rest.call(call)

    def post(
        self,
        forest: str,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/forests/{id|name} endpoint."""
        call = ForestPostCall(forest=forest, body=body)
        return self._rest.call(call)

    def delete(
        self,
        forest: str,
        level: str,
        replicas: str | None = None,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/forests/{id|name} endpoint."""
        call = ForestDeleteCall(forest=forest, level=level, replicas=replicas)
        return self._rest.call(call)

    def get_properties(
        self,
        forest: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/forests/{id|name}/properties."""
        call = ForestPropertiesGetCall(forest=forest, data_format=data_format)
        return self._rest.call(call)

    def put_properties(
        self,
        forest: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/forests/{id|name}/properties."""
        call = ForestPropertiesPutCall(forest=forest, body=body)
        return self._rest.call(call)
