"""The ML Client package.

The root package of Python API to manage MarkLogic instance.

This package exports the following classes:
    * MLClient
        Main entry point for MarkLogic interaction with layered access.
    * AsyncMLClient
        Async variant of MLClient.
    * HttpClient
        A low-level class used to send HTTP requests to a MarkLogic instance.
    * AsyncHttpClient
        Async variant of HttpClient.
    * ApiClient
        A mid-level client providing call() for ApiCall objects.
    * AsyncApiClient
        Async variant of ApiClient.
    * MLEnvironment
        A class representing a MarkLogic configuration environment.
    * MLClientManager
        A high-level class managing MarkLogic clients for a given environment.
    * MLResponseParser
        A MarkLogic HTTP response parser.

This package exports the following functions:
    * find_mlclient_environment
        Locate a named environment's configuration file in the nearest .mlclient.
    * find_mlclient_directory
        Locate the nearest .mlclient directory at a path or in an ancestor.

Examples
--------
>>> from mlclient import MLClient
>>> with MLClient() as ml:
...     resp = ml.manage.databases.get_list()
"""

import logging.config

import yaml
from haggis.logs import add_logging_level

from . import utils
from .auth import AuthConfig, MarkLogicCloudAuth, OAuthBearerAuth
from .clients import (
    DEFAULT_RETRY_STRATEGY,
    MARKLOGIC_ADMIN_PORT,
    MARKLOGIC_APP_SERVICES_PORT,
    MARKLOGIC_HEALTHCHECK_PORT,
    MARKLOGIC_MANAGE_PORT,
    NO_RETRY_STRATEGY,
    RESTART_RETRY_STRATEGY,
    ApiClient,
    AsyncApiClient,
    AsyncHttpClient,
    AsyncMLClient,
    HttpClient,
    MLClient,
)
from .connection import CloudConfig, SSLConfig
from .ml_client_manager import MLClientManager
from .ml_environment import (
    MLEnvironment,
    find_mlclient_directory,
    find_mlclient_environment,
)
from .ml_response_parser import MLResponseParser
from .models.version import MarkLogicVersion


def setup_logger():
    """Set up MLClient logging configuration."""
    with utils.get_resource("logging.yaml") as config_file:
        config = yaml.safe_load(config_file.read())
        logging.config.dictConfig(config)


__version__ = "0.4.1"
__all__ = [
    "DEFAULT_RETRY_STRATEGY",
    "MARKLOGIC_ADMIN_PORT",
    "MARKLOGIC_APP_SERVICES_PORT",
    "MARKLOGIC_HEALTHCHECK_PORT",
    "MARKLOGIC_MANAGE_PORT",
    "NO_RETRY_STRATEGY",
    "RESTART_RETRY_STRATEGY",
    "ApiClient",
    "AsyncApiClient",
    "AsyncHttpClient",
    "AsyncMLClient",
    "AuthConfig",
    "CloudConfig",
    "HttpClient",
    "MLClient",
    "MLClientManager",
    "MLEnvironment",
    "MLResponseParser",
    "MarkLogicCloudAuth",
    "MarkLogicVersion",
    "OAuthBearerAuth",
    "SSLConfig",
    "__version__",
    "find_mlclient_directory",
    "find_mlclient_environment",
    "setup_logger",
]

add_logging_level("FINE", logging.DEBUG - 1)
