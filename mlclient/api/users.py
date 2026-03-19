"""UsersApi - mid-level access to MarkLogic user endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import (
    UserDeleteCall,
    UserGetCall,
    UserPropertiesGetCall,
    UserPropertiesPutCall,
    UsersGetCall,
    UsersPostCall,
)

if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class UsersApi:
    """Mid-level API for /manage/v2/users endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get_list(
        self,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/users endpoint."""
        call = UsersGetCall(data_format=data_format, view=view)
        return self._rest.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/users endpoint."""
        call = UsersPostCall(body=body)
        return self._rest.call(call)

    def get(
        self,
        user: str,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/users/{id|name} endpoint."""
        call = UserGetCall(user=user, data_format=data_format, view=view)
        return self._rest.call(call)

    def delete(
        self,
        user: str,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/users/{id|name} endpoint."""
        call = UserDeleteCall(user=user)
        return self._rest.call(call)

    def get_properties(
        self,
        user: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/users/{id|name}/properties."""
        call = UserPropertiesGetCall(user=user, data_format=data_format)
        return self._rest.call(call)

    def put_properties(
        self,
        user: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/users/{id|name}/properties."""
        call = UserPropertiesPutCall(user=user, body=body)
        return self._rest.call(call)
