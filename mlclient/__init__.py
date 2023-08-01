"""The ML Client package.

The root package of Python API to manage MarkLogic instance. It contains the most
generic modules:
* ml_client
    The ML Client module.
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
    An MLClient subclass supporting internal REST Resources of the MarkLogic server.

Examples
--------
from mlclient import Document, DocumentType, Metadata
"""
from __future__ import annotations

from .ml_client import MLClient, MLResourceClient

__version__ = "0.1.0"
__all__ = ["MLClient", "MLResourceClient"]
