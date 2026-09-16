"""Management API group for /manage/v2/* endpoints (ManageApi / AsyncManageApi).

Requires the Manage server (port 8002 by default).
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.base import ApiCall

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient

from mlclient.api.databases import AsyncDatabasesApi, DatabasesApi
from mlclient.api.forests import AsyncForestsApi, ForestsApi
from mlclient.api.groups import AsyncGroupsApi, GroupsApi
from mlclient.api.hosts import AsyncHostsApi, HostsApi
from mlclient.api.logs import AsyncLogsApi, LogsApi
from mlclient.api.roles import AsyncRolesApi, RolesApi
from mlclient.api.servers import AsyncServersApi, ServersApi
from mlclient.api.users import AsyncUsersApi, UsersApi


class ManageApi:
    """Management API group for /manage/v2/* endpoints.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
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
        return self._api.call(call_, timeout=timeout)

    @cached_property
    def databases(self) -> DatabasesApi:
        """Access databases operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        DatabasesApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return DatabasesApi(self._api)

    @cached_property
    def forests(self) -> ForestsApi:
        """Access forests operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        ForestsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return ForestsApi(self._api)

    @cached_property
    def groups(self) -> GroupsApi:
        """Access groups operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        GroupsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return GroupsApi(self._api)

    @cached_property
    def hosts(self) -> HostsApi:
        """Access hosts operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        HostsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return HostsApi(self._api)

    @cached_property
    def logs(self) -> LogsApi:
        """Access logs operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        LogsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return LogsApi(self._api)

    @cached_property
    def roles(self) -> RolesApi:
        """Access roles operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        RolesApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return RolesApi(self._api)

    @cached_property
    def servers(self) -> ServersApi:
        """Access servers operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        ServersApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return ServersApi(self._api)

    @cached_property
    def users(self) -> UsersApi:
        """Access users operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        UsersApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return UsersApi(self._api)


class AsyncManageApi:
    """Async Management API group for /manage/v2/* endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
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
        return await self._api.call(call_, timeout=timeout)

    @cached_property
    def databases(self) -> AsyncDatabasesApi:
        """Access databases operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncDatabasesApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncDatabasesApi(self._api)

    @cached_property
    def forests(self) -> AsyncForestsApi:
        """Access forests operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncForestsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncForestsApi(self._api)

    @cached_property
    def groups(self) -> AsyncGroupsApi:
        """Access groups operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncGroupsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncGroupsApi(self._api)

    @cached_property
    def hosts(self) -> AsyncHostsApi:
        """Access hosts operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncHostsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncHostsApi(self._api)

    @cached_property
    def logs(self) -> AsyncLogsApi:
        """Access logs operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncLogsApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncLogsApi(self._api)

    @cached_property
    def roles(self) -> AsyncRolesApi:
        """Access roles operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncRolesApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncRolesApi(self._api)

    @cached_property
    def servers(self) -> AsyncServersApi:
        """Access servers operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncServersApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncServersApi(self._api)

    @cached_property
    def users(self) -> AsyncUsersApi:
        """Access users operations through this API group's connection.

        Created once on first access and reused by this group. Reading the
        property sends no request; calling an endpoint method performs I/O
        and returns a raw HTTP response. Responses are not cached.

        Returns
        -------
        AsyncUsersApi
            The endpoint wrapper bound to this group's configured connection.
        """
        return AsyncUsersApi(self._api)
