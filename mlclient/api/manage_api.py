"""Management API group for /manage/v2/* endpoints (ManageApi / AsyncManageApi).

Requires the Manage server (port 8002 by default).
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import ApiCall
from mlclient.connection import UNSET

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient

from .databases import AsyncDatabasesApi, DatabasesApi
from .forests import AsyncForestsApi, ForestsApi
from .groups import AsyncGroupsApi, GroupsApi
from .logs import AsyncLogsApi, LogsApi
from .roles import AsyncRolesApi, RolesApi
from .servers import AsyncServersApi, ServersApi
from .users import AsyncUsersApi, UsersApi


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
        """Return the databases API group."""
        return DatabasesApi(self._api)

    @cached_property
    def forests(self) -> ForestsApi:
        """Return the forests API group."""
        return ForestsApi(self._api)

    @cached_property
    def groups(self) -> GroupsApi:
        """Return the groups API group."""
        return GroupsApi(self._api)

    @cached_property
    def logs(self) -> LogsApi:
        """Return the logs API group."""
        return LogsApi(self._api)

    @cached_property
    def roles(self) -> RolesApi:
        """Return the roles API group."""
        return RolesApi(self._api)

    @cached_property
    def servers(self) -> ServersApi:
        """Return the servers API group."""
        return ServersApi(self._api)

    @cached_property
    def users(self) -> UsersApi:
        """Return the users API group."""
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
        """Return the databases API group."""
        return AsyncDatabasesApi(self._api)

    @cached_property
    def forests(self) -> AsyncForestsApi:
        """Return the forests API group."""
        return AsyncForestsApi(self._api)

    @cached_property
    def groups(self) -> AsyncGroupsApi:
        """Return the groups API group."""
        return AsyncGroupsApi(self._api)

    @cached_property
    def logs(self) -> AsyncLogsApi:
        """Return the logs API group."""
        return AsyncLogsApi(self._api)

    @cached_property
    def roles(self) -> AsyncRolesApi:
        """Return the roles API group."""
        return AsyncRolesApi(self._api)

    @cached_property
    def servers(self) -> AsyncServersApi:
        """Return the servers API group."""
        return AsyncServersApi(self._api)

    @cached_property
    def users(self) -> AsyncUsersApi:
        """Return the users API group."""
        return AsyncUsersApi(self._api)
