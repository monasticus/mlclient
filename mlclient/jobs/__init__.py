"""Experimental document jobs and their progress reports.

Use the documents service for stable document operations.
"""

from mlclient._experimental import EXPERIMENTAL_NOTICE as _EXPERIMENTAL_NOTICE

from mlclient.jobs.documents import (
    DocumentJobReport,
    DocumentReport,
    DocumentStatus,
    DocumentStatusDetails,
    ReadDocumentsJob,
    WriteDocumentsJob,
)

__experimental__ = _EXPERIMENTAL_NOTICE

__all__ = [
    "DocumentJobReport",
    "DocumentReport",
    "DocumentStatus",
    "DocumentStatusDetails",
    "ReadDocumentsJob",
    "WriteDocumentsJob",
]
