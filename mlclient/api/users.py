"""UsersApi / AsyncUsersApi - mid-level access to MarkLogic user endpoints."""

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

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class UsersApi:
    """Mid-level API for ``/manage/v2/users`` endpoints.

    Create, read, update, and delete users in the security database.

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
        """Retrieve a summary of the users in the cluster.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/users

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.

        Returns
        -------
        Response
            An HTTP response with the users summary
        """
        call = UsersGetCall(data_format=data_format, view=view)
        return self._api.call(call)

    def create(
        self,
        body: str | dict,
    ) -> Response:
        """Create a new user in the security database.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/users

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
        return self._api.call(call)

    def get(
        self,
        user: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve the configuration for the specified user.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/users/[id-or-name]

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
            An HTTP response with the user details
        """
        call = UserGetCall(user=user, data_format=data_format, view=view)
        return self._api.call(call)

    def delete(
        self,
        user: str,
    ) -> Response:
        """Delete the specified user from the security database.

        Documentation: https://docs.marklogic.com/REST/DELETE/manage/v2/users/[id-or-name]

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
        return self._api.call(call)

    def get_properties(
        self,
        user: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Retrieve the properties of the specified user.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/users/[id-or-name]/properties

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
            An HTTP response with the user properties
        """
        call = UserPropertiesGetCall(user=user, data_format=data_format)
        return self._api.call(call)

    def put_properties(
        self,
        user: str,
        body: str | dict,
    ) -> Response:
        """Update the properties for the specified user.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/users/[id-or-name]/properties

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
        return self._api.call(call)


class AsyncUsersApi:
    """Async mid-level API for ``/manage/v2/users`` endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve a summary of the users in the cluster."""
        call = UsersGetCall(data_format=data_format, view=view)
        return await self._api.call(call)

    async def create(
        self,
        body: str | dict,
    ) -> Response:
        """Create a new user in the security database."""
        call = UsersPostCall(body=body)
        return await self._api.call(call)

    async def get(
        self,
        user: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Retrieve the configuration for the specified user."""
        call = UserGetCall(user=user, data_format=data_format, view=view)
        return await self._api.call(call)

    async def delete(
        self,
        user: str,
    ) -> Response:
        """Delete the specified user from the security database."""
        call = UserDeleteCall(user=user)
        return await self._api.call(call)

    async def get_properties(
        self,
        user: str,
        *,
        data_format: str | None = None,
    ) -> Response:
        """Retrieve the properties of the specified user."""
        call = UserPropertiesGetCall(user=user, data_format=data_format)
        return await self._api.call(call)

    async def put_properties(
        self,
        user: str,
        body: str | dict,
    ) -> Response:
        """Update the properties for the specified user."""
        call = UserPropertiesPutCall(user=user, body=body)
        return await self._api.call(call)
