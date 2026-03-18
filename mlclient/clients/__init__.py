"""The ML Clients package.

This package contains Python API to connect with MarkLogic server using various clients.
It contains the following modules

    * ml_client
        The ML Client module.
    * documents_client
        The ML Documents Client module.
    * eval_client
        The ML Eval Client module.
    * logs_client
        The ML Logs Client module.

This package exports the following classes:
    * MLClient
        A low-level class used to send simple HTTP requests to a MarkLogic instance.
    * MLResourceClient
        A MLClient subclass calling ResourceCall implementation classes.
    * MLResourcesClient
        A MLResourceClient subclass supporting REST Resources of the MarkLogic server.
    * EvalClient
        An MLResourceClient calling /v1/eval endpoint.
    * LogsClient
        An MLResourceClient calling /manage/v2/logs endpoint.
    * LogType
        An enumeration class representing MarkLogic log types.

Examples
--------
>>> from mlclient.clients import MLResourceClient
"""

from .ml_client import (
    DEFAULT_RETRY_STRATEGY,
    MARKLOGIC_ADMIN_API_PORT,
    MARKLOGIC_MANAGE_API_PORT,
    MARKLOGIC_REST_API_PORT,
    RESTART_RETRY_STRATEGY,
    MLClient,
    MLResourceClient,
    MLResourcesClient,
)
from .documents_client import DocumentsClient
from .eval_client import EvalClient, LOCAL_NS
from .logs_client import LogsClient, LogType

__all__ = [
    "DEFAULT_RETRY_STRATEGY",
    "LOCAL_NS",
    "MARKLOGIC_ADMIN_API_PORT",
    "MARKLOGIC_MANAGE_API_PORT",
    "MARKLOGIC_REST_API_PORT",
    "RESTART_RETRY_STRATEGY",
    "DocumentsClient",
    "EvalClient",
    "LogType",
    "LogsClient",
    "MLClient",
    "MLResourceClient",
    "MLResourcesClient",
]
