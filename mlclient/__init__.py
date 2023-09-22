"""The ML Client package.

The root package of Python API to manage MarkLogic instance. It contains the most
generic modules:

    * ml_config
        The ML Configuration module.
    * ml_manager
        The ML Manager module.
    * constants
        The ML Client Constants module.
    * exceptions
        The ML Client Exceptions module.
    * utils
        The ML Client Utils module.

This package exports the following classes:
    * MLClient
        A low-level class used to send simple HTTP requests to a MarkLogic instance.
    * MLResourceClient
        A MLClient subclass calling ResourceCall implementation classes.
    * MLResourcesClient
        A MLResourceClient subclass supporting REST Resources of the MarkLogic server.
    * MLResponseParser
        A MarkLogic HTTP response parser.
    * MLConfiguration
        A class representing MarkLogic configuration.
    * MLManager
        A high-level class managing a MarkLogic instance.

Examples
--------
>>> from mlclient import MLResourcesClient
"""
from .clients import (LOCAL_NS, MLClient, MLResourceClient, MLResourcesClient,
                      MLResponseParser)
from .ml_config import MLConfiguration
from .ml_manager import MLManager

__version__ = "0.3.1"
__all__ = ["__version__", "LOCAL_NS",
           "MLClient", "MLResourceClient", "MLResourcesClient", "MLResponseParser",
           "MLConfiguration", "MLManager"]
