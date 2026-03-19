"""REST API group for /v1/* endpoints.

Requires a REST app server.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import RestCall

# Avoid circular import: RestClient -> api classes -> RestClient
if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient

from .documents import DocumentsApi
from .eval import EvalApi


class RestApi:
    """REST API group for /v1/* endpoints (eval, documents).

    Requires a REST app server.
    """

    def __init__(self, client: RestClient):
        self._client = client

    def call(self, call_: RestCall) -> Response:
        """Send a custom RestCall.

        Parameters
        ----------
        call_ : RestCall
            A specific endpoint call implementation

        Returns
        -------
        Response
            An HTTP response
        """
        return self._client.call(call_)

    @cached_property
    def eval(self) -> EvalApi:
        """Return the eval API group."""
        return EvalApi(self._client)

    @cached_property
    def documents(self) -> DocumentsApi:
        """Return the documents API group."""
        return DocumentsApi(self._client)
