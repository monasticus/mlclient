"""Expose a hypothetical application endpoint through sync and async clients."""

from functools import cached_property

from mlclient import AsyncMLClient, MLClient
from mlclient.api import AsyncRestApi, RestApi
from mlclient.calls import ApiCall
from mlclient.clients import ApiClient, AsyncApiClient
from mlclient.http import UNSET


class TasksGetCall(ApiCall):
    """Describe GET /app/tasks without performing I/O."""

    def __init__(self, status="open"):
        """Set the requested task status and JSON response negotiation."""
        super().__init__(params={"status": status}, accept="application/json")

    @property
    def endpoint(self):
        """Return the application's deployed route."""
        return "/app/tasks"


class MyAppRestApi(RestApi):
    """Add a named application operation beside the built-in REST APIs."""

    def my_awesome_endpoint(self, status="open", *, timeout=UNSET):
        """Return the raw task response; forward the per-request timeout."""
        return self.call(TasksGetCall(status), timeout=timeout)


class MyAppMLClient(MLClient):
    """Reuse the parent connection and lifecycle for an application API."""

    @cached_property
    def rest(self):
        """Access the application's extended REST API."""
        return MyAppRestApi(ApiClient(self.http))


class AsyncMyAppRestApi(AsyncRestApi):
    """Provide the same task operation through async HTTP."""

    async def my_awesome_endpoint(self, status="open", *, timeout=UNSET):
        """Return the raw task response without blocking the event loop."""
        return await self.call(TasksGetCall(status), timeout=timeout)


class AsyncMyAppMLClient(AsyncMLClient):
    """Expose the application API with the parent's async session ownership."""

    @cached_property
    def rest(self):
        """Access the application's extended async REST API."""
        return AsyncMyAppRestApi(AsyncApiClient(self.http))
