"""A client extension for an application's hypothetical /app/tasks endpoint."""

from functools import cached_property

from mlclient import AsyncMLClient, MLClient
from mlclient.api import AsyncRestApi, RestApi
from mlclient.calls import ApiCall
from mlclient.clients import ApiClient, AsyncApiClient
from mlclient.http import UNSET


class TasksGetCall(ApiCall):
    """Describe a request for application tasks; perform no network I/O."""

    def __init__(self, status="open"):
        super().__init__(params={"status": status}, accept="application/json")

    @property
    def endpoint(self):
        return "/app/tasks"


class TasksApi:
    """Return the application's raw HTTP response, like the built-in REST APIs."""

    def __init__(self, api):
        self._api = api

    def list(self, status="open", *, timeout=UNSET):
        return self._api.call(TasksGetCall(status), timeout=timeout)


class AppRestApi(RestApi):
    """The built-in REST APIs plus the application's tasks endpoint."""

    @cached_property
    def tasks(self):
        return TasksApi(self._api)


class TasksService:
    """Turn task responses into parsed Python values."""

    def __init__(self, rest):
        self._rest = rest

    def open_titles(self, *, timeout=UNSET):
        response = self._rest.tasks.list(timeout=timeout)
        response.raise_for_status()
        return [task["title"] for task in response.json()["tasks"]]


class AppClient(MLClient):
    """Expose tasks as raw HTTP on ``.rest.tasks`` and parsed on ``.tasks``."""

    @cached_property
    def rest(self):
        return AppRestApi(ApiClient(self.http))

    @cached_property
    def tasks(self):
        return TasksService(self.rest)


class AsyncTasksApi:
    """Return the application's raw response without blocking the event loop."""

    def __init__(self, api):
        self._api = api

    async def list(self, status="open", *, timeout=UNSET):
        return await self._api.call(TasksGetCall(status), timeout=timeout)


class AsyncAppRestApi(AsyncRestApi):
    """The built-in async REST APIs plus the application's tasks endpoint."""

    @cached_property
    def tasks(self):
        return AsyncTasksApi(self._api)


class AsyncTasksService:
    """Turn task responses into parsed Python values without blocking."""

    def __init__(self, rest):
        self._rest = rest

    async def open_titles(self, *, timeout=UNSET):
        response = await self._rest.tasks.list(timeout=timeout)
        response.raise_for_status()
        return [task["title"] for task in response.json()["tasks"]]


class AsyncAppClient(AsyncMLClient):
    """An async client with the same two-layer application operations."""

    @cached_property
    def rest(self):
        return AsyncAppRestApi(AsyncApiClient(self.http))

    @cached_property
    def tasks(self):
        return AsyncTasksService(self.rest)
