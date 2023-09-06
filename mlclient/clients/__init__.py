"""The ML Clients package.

This package contains Python API to connect with MarkLogic server using carious clients.
It contains the following modules

    * ml_client
        The ML Client module.
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
    * MLResponseParser
        A MarkLogic HTTP response parser.
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
from .ml_client import (MLClient, MLResourceClient, MLResourcesClient,
                        MLResponseParser)
from .eval_client import EvalClient, LOCAL_NS
from .logs_client import LogsClient, LogType

__all__ = ["EvalClient", "LOCAL_NS",
           "LogType", "LogsClient",
           "MLClient", "MLResourceClient", "MLResourcesClient",
           "MLResponseParser"]
