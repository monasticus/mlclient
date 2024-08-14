"""The ML Jobs package.

This package contains Python API to perform various operations.
It contains the following modules

    * documents_jobs
        The ML Documents Jobs module.

This package exports the following classes:
    * WriteDocumentsJob
        A multi-thread job writing documents into a MarkLogic database.
    * ReadDocumentsJob
        A multi-thread job reading documents from a MarkLogic database.
    * DocumentJobReport
        A class representing a documents job report.
    * DocumentsLoader
        A class parsing files into Documents.

Examples
--------
>>> from mlclient.jobs import WriteDocumentsJob
"""

from .documents_jobs import (
    DocumentJobReport,
    DocumentsLoader,
    ReadDocumentsJob,
    WriteDocumentsJob,
)

__all__ = [
    "DocumentJobReport",
    "ReadDocumentsJob",
    "WriteDocumentsJob",
    "DocumentsLoader",
]
