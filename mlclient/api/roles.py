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

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient


class RolesApi:
    """Mid-level API for /manage/v2/roles endpoints."""

    def __init__(self, rest: ApiClient):
        self._rest = rest

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/roles endpoint.

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
        call = RolesGetCall(data_format=data_format, view=view)
        return self._rest.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/roles endpoint.

        Parameters
        ----------
        body : str | dict
            A role properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RolesPostCall(body=body)
        return self._rest.call(call)

    def get(
        self,
        role: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/roles/{id|name} endpoint.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
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
        call = RoleGetCall(role=role, data_format=data_format, view=view)
        return self._rest.call(call)

    def delete(
        self,
        role: str,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/roles/{id|name} endpoint.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RoleDeleteCall(role=role)
        return self._rest.call(call)

    def get_properties(
        self,
        role: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/roles/{id|name}/properties.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RolePropertiesGetCall(role=role, data_format=data_format)
        return self._rest.call(call)

    def put_properties(
        self,
        role: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/roles/{id|name}/properties.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        body : str | dict
            A role properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RolePropertiesPutCall(role=role, body=body)
        return self._rest.call(call)
