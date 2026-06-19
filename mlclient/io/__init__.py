"""The ML I/O package.

This package contains utilities for loading and serializing documents from/to
external sources (e.g. the filesystem). It contains the following modules:

    * documents_loader
        The ML Documents Loader module.
    * documents_writer
        The ML Documents Writer module.

This package exports the following classes:
    * DocumentsLoader
        A class parsing files into Documents.
    * DocumentsWriter
        A class serializing Documents into files.

Examples
--------
>>> from mlclient.io import DocumentsLoader, DocumentsWriter
"""

from .documents_loader import DocumentsLoader
from .documents_writer import DocumentsWriter

__all__ = [
    "DocumentsLoader",
    "DocumentsWriter",
]
