"""RolesApi - mid-level access to MarkLogic role endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import (
    RoleDeleteCall,
    RoleGetCall,
    RolePropertiesGetCall,
    RolePropertiesPutCall,
    RolesGetCall,
    RolesPostCall,
)

# Avoid circular import: RestClient -> api classes -> RestClient
if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class RolesApi:
    """Mid-level API for /manage/v2/roles endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get_list(
        self,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/roles endpoint."""
        call = RolesGetCall(data_format=data_format, view=view)
        return self._rest.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/roles endpoint."""
        call = RolesPostCall(body=body)
        return self._rest.call(call)

    def get(
        self,
        role: str,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/roles/{id|name} endpoint."""
        call = RoleGetCall(role=role, data_format=data_format, view=view)
        return self._rest.call(call)

    def delete(
        self,
        role: str,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/roles/{id|name} endpoint."""
        call = RoleDeleteCall(role=role)
        return self._rest.call(call)

    def get_properties(
        self,
        role: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/roles/{id|name}/properties."""
        call = RolePropertiesGetCall(role=role, data_format=data_format)
        return self._rest.call(call)

    def put_properties(
        self,
        role: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/roles/{id|name}/properties."""
        call = RolePropertiesPutCall(role=role, body=body)
        return self._rest.call(call)
