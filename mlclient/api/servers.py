"""ServersApi - mid-level access to MarkLogic server endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import (
    ServerDeleteCall,
    ServerGetCall,
    ServerPropertiesGetCall,
    ServerPropertiesPutCall,
    ServersGetCall,
    ServersPostCall,
)

if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class ServersApi:
    """Mid-level API for /manage/v2/servers endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get_list(
        self,
        data_format: str | None = None,
        group_id: str | None = None,
        view: str | None = None,
        full_refs: bool | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/servers endpoint."""
        call = ServersGetCall(
            data_format=data_format,
            group_id=group_id,
            view=view,
            full_refs=full_refs,
        )
        return self._rest.call(call)

    def create(
        self,
        body: str | dict,
        group_id: str | None = None,
        server_type: str | None = None,
    ) -> Response:
        """Send a POST request to the /manage/v2/servers endpoint."""
        call = ServersPostCall(body=body, group_id=group_id, server_type=server_type)
        return self._rest.call(call)

    def get(
        self,
        server: str,
        group_id: str,
        data_format: str | None = None,
        view: str | None = None,
        host_id: str | None = None,
        full_refs: bool | None = None,
        modules: bool | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/servers/{id|name} endpoint."""
        call = ServerGetCall(
            server=server,
            group_id=group_id,
            data_format=data_format,
            view=view,
            host_id=host_id,
            full_refs=full_refs,
            modules=modules,
        )
        return self._rest.call(call)

    def delete(
        self,
        server: str,
        group_id: str,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/servers/{id|name} endpoint."""
        call = ServerDeleteCall(server=server, group_id=group_id)
        return self._rest.call(call)

    def get_properties(
        self,
        server: str,
        group_id: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/servers/{id|name}/properties."""
        call = ServerPropertiesGetCall(
            server=server,
            group_id=group_id,
            data_format=data_format,
        )
        return self._rest.call(call)

    def put_properties(
        self,
        server: str,
        group_id: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/servers/{id|name}/properties."""
        call = ServerPropertiesPutCall(server=server, group_id=group_id, body=body)
        return self._rest.call(call)
