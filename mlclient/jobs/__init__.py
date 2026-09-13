"""The ML Jobs package.

This package is experimental, including job configuration and report models.
Its API may change in minor releases and is excluded from the 1.x stability
contract. Constructing a job emits a warning through Python logging; importing
the package does not. Prefer MLClient.documents or AsyncMLClient.documents for
stable document operations.
It contains the following modules

    * documents_jobs
        The ML Documents Jobs module.

This package exports the following classes:
    * WriteDocumentsJob
        An async job writing documents into a MarkLogic database.
    * ReadDocumentsJob
        An async job reading documents from a MarkLogic database.
    * DocumentJobReport
        A class representing a documents job report.

Examples
--------
>>> from mlclient.jobs import WriteDocumentsJob
"""

from .documents_jobs import DocumentJobReport, ReadDocumentsJob, WriteDocumentsJob

__all__ = [
    "DocumentJobReport",
    "ReadDocumentsJob",
    "WriteDocumentsJob",
]
