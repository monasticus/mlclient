"""RolesApi / AsyncRolesApi - mid-level access to MarkLogic role endpoints."""

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
    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class RolesApi:
    """Mid-level API for ``/manage/v2/roles`` endpoints.

    Create, read, update, and delete roles in the security database.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve a summary of the roles in the security database.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/roles

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.

        Returns
        -------
        Response
            An HTTP response with the roles summary
        """
        call = RolesGetCall(data_format=data_format, view=view)
        return self._api.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Create a new role in the security database.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/roles

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
        return self._api.call(call)

    def get(
        self,
        role: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve the configuration for the specified role.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/roles/[id-or-name]

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
            An HTTP response with the role details
        """
        call = RoleGetCall(role=role, data_format=data_format, view=view)
        return self._api.call(call)

    def delete(
        self,
        role: str,
    ) -> Response:
        """Delete the specified role from the security database.

        Documentation: https://docs.marklogic.com/REST/DELETE/manage/v2/roles/[id-or-name]

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
        return self._api.call(call)

    def get_properties(
        self,
        role: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Retrieve the properties of the specified role.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/roles/[id-or-name]/properties

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
            An HTTP response with the role properties
        """
        call = RolePropertiesGetCall(role=role, data_format=data_format)
        return self._api.call(call)

    def put_properties(
        self,
        role: str,
        body: str | dict,
    ) -> Response:
        """Update the properties for the specified role.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/roles/[id-or-name]/properties

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
        return self._api.call(call)


class AsyncRolesApi:
    """Async mid-level API for ``/manage/v2/roles`` endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve a summary of the roles in the security database."""
        call = RolesGetCall(data_format=data_format, view=view)
        return await self._api.call(call)

    async def create(
        self,
        body: str | dict,
    ) -> Response:
        """Create a new role in the security database."""
        call = RolesPostCall(body=body)
        return await self._api.call(call)

    async def get(
        self,
        role: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve the configuration for the specified role."""
        call = RoleGetCall(role=role, data_format=data_format, view=view)
        return await self._api.call(call)

    async def delete(
        self,
        role: str,
    ) -> Response:
        """Delete the specified role from the security database."""
        call = RoleDeleteCall(role=role)
        return await self._api.call(call)

    async def get_properties(
        self,
        role: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Retrieve the properties of the specified role."""
        call = RolePropertiesGetCall(role=role, data_format=data_format)
        return await self._api.call(call)

    async def put_properties(
        self,
        role: str,
        body: str | dict,
    ) -> Response:
        """Update the properties for the specified role."""
        call = RolePropertiesPutCall(role=role, body=body)
        return await self._api.call(call)
