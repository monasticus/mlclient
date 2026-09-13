"""A client extension for an application's hypothetical /app/tasks endpoint."""

from functools import cached_property

from mlclient import ApiClient, AsyncApiClient, AsyncMLClient, MLClient
from mlclient.calls import ApiCall
from mlclient.connection import UNSET


class TasksGetCall(ApiCall):
    """Describe a request for application tasks; perform no network I/O."""

    def __init__(self, status="open"):
        super().__init__(params={"status": status}, accept="application/json")

    @property
    def endpoint(self):
        return "/app/tasks"


class TasksApi:
    """Expose the application's raw HTTP response."""

    def __init__(self, api):
        self.api = api

    def list(self, status="open", *, timeout=UNSET):
        return self.api.call(TasksGetCall(status), timeout=timeout)


class AppClient(MLClient):
    """Add application operations while retaining the built-in client APIs."""

    @cached_property
    def tasks(self):
        return TasksApi(ApiClient(self.http))

    def open_task_titles(self, *, timeout=UNSET):
        response = self.tasks.list(timeout=timeout)
        response.raise_for_status()
        return [task["title"] for task in response.json()["tasks"]]


class AsyncTasksApi:
    """Expose the application's raw response without blocking the event loop."""

    def __init__(self, api):
        self.api = api

    async def list(self, status="open", *, timeout=UNSET):
        return await self.api.call(TasksGetCall(status), timeout=timeout)


class AsyncAppClient(AsyncMLClient):
    """An async client with the same application operations."""

    @cached_property
    def tasks(self):
        return AsyncTasksApi(AsyncApiClient(self.http))

    async def open_task_titles(self, *, timeout=UNSET):
        response = await self.tasks.list(timeout=timeout)
        response.raise_for_status()
        return [task["title"] for task in response.json()["tasks"]]
