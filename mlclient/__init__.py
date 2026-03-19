"""The ML Client package.

The root package of Python API to manage MarkLogic instance.

This package exports the following classes:
    * MLClient
        Main entry point for MarkLogic interaction with layered access.
    * HttpClient
        A low-level class used to send HTTP requests to a MarkLogic instance.
    * RestClient
        A mid-level client providing call() for RestCall objects.
    * MLConfiguration
        A class representing MarkLogic configuration.
    * MLManager
        A high-level class managing a MarkLogic instance.
    * MLResponseParser
        A MarkLogic HTTP response parser.

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
from .clients import (
    DEFAULT_RETRY_STRATEGY,
    MARKLOGIC_ADMIN_API_PORT,
    MARKLOGIC_MANAGE_API_PORT,
    MARKLOGIC_REST_API_PORT,
    RESTART_RETRY_STRATEGY,
    HttpClient,
    MLClient,
    RestClient,
)
from .ml_config import MLConfiguration
from .ml_manager import MLManager
from .ml_response_parser import MLResponseParser


def setup_logger():
    """Set up MLClient logging configuration."""
    with utils.get_resource("logging.yaml") as config_file:
        config = yaml.safe_load(config_file.read())
        logging.config.dictConfig(config)


__version__ = "0.4.1"
__all__ = [
    "DEFAULT_RETRY_STRATEGY",
    "MARKLOGIC_ADMIN_API_PORT",
    "MARKLOGIC_MANAGE_API_PORT",
    "MARKLOGIC_REST_API_PORT",
    "RESTART_RETRY_STRATEGY",
    "HttpClient",
    "MLClient",
    "MLConfiguration",
    "MLManager",
    "MLResponseParser",
    "RestClient",
    "__version__",
    "setup_logger",
]

add_logging_level("FINE", logging.DEBUG - 1)
