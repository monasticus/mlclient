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

# Avoid circular import: RestClient -> api classes -> RestClient
if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class UsersApi:
    """Mid-level API for /manage/v2/users endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/users endpoint.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UsersGetCall(data_format=data_format, view=view)
        return self._rest.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/users endpoint.

        Parameters
        ----------
        body : str | dict
            A user properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UsersPostCall(body=body)
        return self._rest.call(call)

    def get(
        self,
        user: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/users/{id|name} endpoint.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data. Can be: describe, or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UserGetCall(user=user, data_format=data_format, view=view)
        return self._rest.call(call)

    def delete(
        self,
        user: str,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/users/{id|name} endpoint.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UserDeleteCall(user=user)
        return self._rest.call(call)

    def get_properties(
        self,
        user: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/users/{id|name}/properties.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UserPropertiesGetCall(user=user, data_format=data_format)
        return self._rest.call(call)

    def put_properties(
        self,
        user: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/users/{id|name}/properties.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        body : str | dict
            A user properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UserPropertiesPutCall(user=user, body=body)
        return self._rest.call(call)
