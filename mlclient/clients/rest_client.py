"""The REST Client module.

It exports the RestClient class for calling MarkLogic REST endpoints
via RestCall objects and organized API groups.
"""

from __future__ import annotations

from functools import cached_property

from httpx import Response

from mlclient.api.databases import DatabasesApi
from mlclient.api.documents import DocumentsApi
from mlclient.api.eval import EvalApi
from mlclient.api.forests import ForestsApi
from mlclient.api.logs import LogsApi
from mlclient.api.roles import RolesApi
from mlclient.api.servers import ServersApi
from mlclient.api.users import UsersApi
from mlclient.calls import ResourceCall

from .http_client import HttpClient


class RestClient:
    """Mid-level client providing call() and endpoint-grouped API access.

    Attributes
    ----------
    http : HttpClient
        The underlying HTTP client used for requests.
    """

    def __init__(self, http: HttpClient):
        self._http = http

    @property
    def http(self) -> HttpClient:
        """Return the underlying HTTP client."""
        return self._http

    def call(self, resource_call: ResourceCall) -> Response:
        """Send a request using a ResourceCall object.

        Parameters
        ----------
        resource_call : ResourceCall
            A specific endpoint call implementation

        Returns
        -------
        Response
            An HTTP response
        """
        return self._http.request(
            method=resource_call.method,
            endpoint=resource_call.endpoint,
            params=resource_call.params,
            headers=resource_call.headers,
            body=resource_call.body,
        )

    @cached_property
    def databases(self) -> DatabasesApi:
        """Return the databases API group."""
        return DatabasesApi(self)

    @cached_property
    def documents(self) -> DocumentsApi:
        """Return the documents API group."""
        return DocumentsApi(self)

    @cached_property
    def eval(self) -> EvalApi:
        """Return the eval API group."""
        return EvalApi(self)

    @cached_property
    def forests(self) -> ForestsApi:
        """Return the forests API group."""
        return ForestsApi(self)

    @cached_property
    def logs(self) -> LogsApi:
        """Return the logs API group."""
        return LogsApi(self)

    @cached_property
    def roles(self) -> RolesApi:
        """Return the roles API group."""
        return RolesApi(self)

    @cached_property
    def servers(self) -> ServersApi:
        """Return the servers API group."""
        return ServersApi(self)

    @cached_property
    def users(self) -> UsersApi:
        """Return the users API group."""
        return UsersApi(self)
