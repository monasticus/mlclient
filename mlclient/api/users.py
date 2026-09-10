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
from mlclient.connection import UNSET

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
        timeout=UNSET,
    ) -> Response:
        """Retrieve a summary of the users in the cluster.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/users

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the users summary

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UsersGetCall(data_format=data_format, view=view)
        return self._api.call(call, timeout=timeout)

    def create(
        self,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Create a new user in the security database.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/users

        Parameters
        ----------
        body : str | dict
            A user properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UsersPostCall(body=body)
        return self._api.call(call, timeout=timeout)

    def get(
        self,
        user: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
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
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the user details

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UserGetCall(user=user, data_format=data_format, view=view)
        return self._api.call(call, timeout=timeout)

    def delete(
        self,
        user: str,
        *,
        timeout=UNSET,
    ) -> Response:
        """Delete the specified user from the security database.

        Documentation: https://docs.marklogic.com/REST/DELETE/manage/v2/users/[id-or-name]

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UserDeleteCall(user=user)
        return self._api.call(call, timeout=timeout)

    def get_properties(
        self,
        user: str,
        *,
        data_format: str | None = None,
        timeout=UNSET,
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
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the user properties

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UserPropertiesGetCall(user=user, data_format=data_format)
        return self._api.call(call, timeout=timeout)

    def put_properties(
        self,
        user: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Update the properties for the specified user.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/users/[id-or-name]/properties

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        body : str | dict
            A user properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UserPropertiesPutCall(user=user, body=body)
        return self._api.call(call, timeout=timeout)


class AsyncUsersApi:
    """Async mid-level API for ``/manage/v2/users`` endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def get_list(
        self,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Retrieve a summary of the users in the cluster.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/users

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the users summary

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UsersGetCall(data_format=data_format, view=view)
        return await self._api.call(call, timeout=timeout)

    async def create(
        self,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Create a new user in the security database.

        Documentation: https://docs.marklogic.com/REST/POST/manage/v2/users

        Parameters
        ----------
        body : str | dict
            A user properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UsersPostCall(body=body)
        return await self._api.call(call, timeout=timeout)

    async def get(
        self,
        user: str,
        *,
        data_format: str | None = None,
        view: str | None = None,
        timeout=UNSET,
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
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the user details

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UserGetCall(user=user, data_format=data_format, view=view)
        return await self._api.call(call, timeout=timeout)

    async def delete(
        self,
        user: str,
        *,
        timeout=UNSET,
    ) -> Response:
        """Delete the specified user from the security database.

        Documentation: https://docs.marklogic.com/REST/DELETE/manage/v2/users/[id-or-name]

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UserDeleteCall(user=user)
        return await self._api.call(call, timeout=timeout)

    async def get_properties(
        self,
        user: str,
        *,
        data_format: str | None = None,
        timeout=UNSET,
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
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the user properties

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UserPropertiesGetCall(user=user, data_format=data_format)
        return await self._api.call(call, timeout=timeout)

    async def put_properties(
        self,
        user: str,
        body: str | dict,
        *,
        timeout=UNSET,
    ) -> Response:
        """Update the properties for the specified user.

        Documentation: https://docs.marklogic.com/REST/PUT/manage/v2/users/[id-or-name]/properties

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        body : str | dict
            A user properties in XML or JSON format.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = UserPropertiesPutCall(user=user, body=body)
        return await self._api.call(call, timeout=timeout)
