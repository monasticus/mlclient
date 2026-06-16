"""The ML Documents Jobs module.

It exports high-level class to perform bulk operations in a MarkLogic server:
    * WriteDocumentsJob
        An async job writing documents into a MarkLogic database.
    * ReadDocumentsJob
        An async job reading documents from a MarkLogic database.
    * DocumentJobReport
        A class representing a documents job report.
    * DocumentReport
        A class representing a document's report.
    * DocumentStatus
        A document's status enum.
    * DocumentStatusDetails
        A class representing a document's status details.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from copy import copy
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from mlclient.clients import AsyncMLClient
from mlclient.io import DocumentsLoader, DocumentsWriter
from mlclient.models import Document
from mlclient.models.http import Category

logger = logging.getLogger(__name__)


class WriteDocumentsJob:
    """An async job writing documents into a MarkLogic database.

    Uses asyncio with a concurrency-limited semaphore to send document batches
    in parallel via AsyncMLClient.

    Recommended settings based on benchmarks (1000 documents):
        concurrency: 4-12 (default: 8)
        batch_size: 50-200 (default: 100)
    """

    def __init__(
        self,
        concurrency: int | None = None,
        batch_size: int = 100,
    ):
        """Initialize WriteDocumentsJob instance.

        Parameters
        ----------
        concurrency : int | None, default None
            Maximum number of concurrent batch requests (default: 8)
        batch_size : int, default 100
            A number of documents in a single batch
        """
        self._concurrency: int = concurrency or 8
        self._batch_size: int = batch_size
        self._config: dict = {}
        self._database: str | None = None
        self._documents: list[Document] = []
        self._report = DocumentJobReport()

    @property
    def report(self) -> DocumentJobReport:
        """A status of the job."""
        return copy(self._report)

    def with_client_config(self, **config):
        """Set AsyncMLClient configuration."""
        self._config = config

    def with_database(self, database: str):
        """Set a database name."""
        self._database = database

    def with_documents_input(self, documents: Iterable[Document]):
        """Add Documents to the job's input."""
        self._documents.extend(documents)

    def with_filesystem_input(self, path: str, uri_prefix: str = ""):
        """Load files and add parsed Documents to the job's input."""
        self._documents.extend(DocumentsLoader.load(path, uri_prefix))

    async def run(self) -> DocumentJobReport:
        """Execute the job and return a report when complete."""
        for doc in self._documents:
            self._report.add_pending_doc(doc.uri)

        batches = [
            self._documents[i : i + self._batch_size]
            for i in range(0, len(self._documents), self._batch_size)
        ]

        sem = asyncio.Semaphore(self._concurrency)
        async with AsyncMLClient(**self._config) as ml:
            await asyncio.gather(
                *(self._send_batch(sem, batch, ml) for batch in batches),
            )

        return copy(self._report)

    def run_sync(self) -> DocumentJobReport:
        """Execute the job synchronously.

        Wrapper around asyncio.run(self.run()). Cannot be called from within
        a running event loop.
        """
        return asyncio.run(self.run())

    async def _send_batch(
        self,
        sem: asyncio.Semaphore,
        batch: list[Document],
        ml: AsyncMLClient,
    ):
        """Send a documents batch to /v1/documents endpoint."""
        batch_uris = [doc.uri for doc in batch]
        async with sem:
            try:
                await ml.documents.write(batch, database=self._database)
                self._report.add_successful_docs(batch_uris)
            except Exception as err:
                self._report.add_failed_docs(batch_uris, err)
                logger.exception(
                    "An unexpected error occurred while writing documents",
                )


class ReadDocumentsJob:
    """An async job reading documents from a MarkLogic database.

    Uses asyncio with a concurrency-limited semaphore to send URI batches
    in parallel via AsyncMLClient.

    Recommended settings based on benchmarks (10000 documents):
        concurrency: 8-24 (default: 16)
        batch_size: 300-1000 (default: 400)
    Higher concurrency combined with larger batch sizes yields the best
    read throughput, with improvements of 30-40% over synchronous execution.
    """

    def __init__(
        self,
        concurrency: int | None = None,
        batch_size: int = 400,
    ):
        """Initialize ReadDocumentsJob instance.

        Parameters
        ----------
        concurrency : int | None, default None
            Maximum number of concurrent batch requests (default: 16)
        batch_size : int, default 400
            A number of URIs in a single batch
        """
        self._concurrency: int = concurrency or 16
        self._batch_size: int = batch_size
        self._config: dict = {}
        self._database: str | None = None
        self._uris: list[str] = []
        self._categories: list[str] = ["content"]
        self._fs_output_path: Path | None = None
        self._documents: list[Document] = []
        self._report = DocumentJobReport()

    @property
    def report(self) -> DocumentJobReport:
        """A status of the job."""
        return copy(self._report)

    @property
    def documents(self) -> list[Document]:
        """Return all read documents from the job."""
        return list(self._documents)

    def with_client_config(self, **config):
        """Set AsyncMLClient configuration."""
        self._config = config

    def with_database(self, database: str):
        """Set a database name."""
        self._database = database

    def with_metadata(self, *args: Category | str):
        """Add metadata category/ies to retrieve from a MarkLogic server."""
        if len(args) == 0:
            self._categories.append("metadata")
        else:
            self._categories.extend(
                c.value if isinstance(c, Category) else c for c in args
            )

    def with_uris_input(self, uris: Iterable[str]):
        """Add URIs to the job's input."""
        self._uris.extend(uris)

    def with_filesystem_output(self, output_path: str):
        """Set filesystem output directory to save documents inside."""
        self._fs_output_path = Path(output_path).resolve().absolute()

    async def run(self) -> DocumentJobReport:
        """Execute the job and return a report when complete."""
        for uri in self._uris:
            self._report.add_pending_doc(uri)

        batches = [
            self._uris[i : i + self._batch_size]
            for i in range(0, len(self._uris), self._batch_size)
        ]

        sem = asyncio.Semaphore(self._concurrency)
        async with AsyncMLClient(**self._config) as ml:
            await asyncio.gather(
                *(self._send_batch(sem, batch, ml) for batch in batches),
            )

        if self._fs_output_path is not None:
            await self._save_documents()

        return copy(self._report)

    def run_sync(self) -> DocumentJobReport:
        """Execute the job synchronously.

        Wrapper around asyncio.run(self.run()). Cannot be called from within
        a running event loop.
        """
        return asyncio.run(self.run())

    async def _send_batch(
        self,
        sem: asyncio.Semaphore,
        batch: list[str],
        ml: AsyncMLClient,
    ):
        """Send a URIs batch to /v1/documents endpoint."""
        async with sem:
            try:
                kwargs = {"database": self._database}
                if self._categories != ["content"]:
                    kwargs["category"] = list(dict.fromkeys(self._categories))
                async for doc in ml.documents.read_stream(batch, **kwargs):
                    self._report.add_successful_doc(doc.uri)
                    self._documents.append(doc)
            except Exception as err:
                self._report.add_failed_docs(batch, err)
                logger.exception(
                    "An unexpected error occurred while reading documents",
                )

    async def _save_documents(self):
        """Save read documents to the filesystem."""
        for doc in self._documents:
            await self._save_document(doc)

    async def _save_document(self, doc: Document):
        """Save a single document to the filesystem, reporting any failure."""
        try:
            await DocumentsWriter.write_document(doc, self._fs_output_path)
        except Exception as err:
            self._report.add_failed_doc(doc.uri, err)


class DocumentJobReport:
    """A class representing documents job report."""

    def __init__(
        self,
    ):
        """Initialize DocumentJobReport instance."""
        self._doc_reports: dict[str, DocumentReport] = {}

    def __copy__(self):
        """Copy DocumentJobReport instance."""
        report_copy = self.__class__()
        for report in self._doc_reports.values():
            report_copy.add_doc_report(report)
        return report_copy

    @property
    def pending(
        self,
    ) -> int:
        """Return number of pending documents."""
        return len(self.pending_docs)

    @property
    def completed(
        self,
    ) -> int:
        """Return number of completed documents."""
        return self.successful + self.failed

    @property
    def successful(
        self,
    ) -> int:
        """Return number of successfully completed documents."""
        return len(self.successful_docs)

    @property
    def failed(
        self,
    ) -> int:
        """Return number of completed documents that failed."""
        return len(self.failed_docs)

    @property
    def pending_docs(
        self,
    ) -> list[str]:
        """Return pending documents' URIs."""
        return self._get_docs_by_status(DocumentStatus.pending)

    @property
    def successful_docs(
        self,
    ) -> list[str]:
        """Return successfully completed documents' URIs."""
        return self._get_docs_by_status(DocumentStatus.success)

    @property
    def failed_docs(
        self,
    ) -> list[str]:
        """Return completed documents' URIs that failed."""
        return self._get_docs_by_status(DocumentStatus.failure)

    @property
    def full(
        self,
    ) -> dict[str, DocumentReport]:
        """Return full documents job report."""
        return {
            uri: report.model_copy(deep=True)
            for uri, report in self._doc_reports.items()
        }

    def add_pending_docs(
        self,
        uris: list[str],
    ):
        """Add pending documents' reports."""
        for uri in uris:
            self.add_pending_doc(uri)

    def add_successful_docs(
        self,
        uris: list[str],
    ):
        """Add successfully completed documents' reports."""
        for uri in uris:
            self.add_successful_doc(uri)

    def add_failed_docs(
        self,
        uris: list[str],
        err: Exception,
    ):
        """Add failed documents' reports."""
        for uri in uris:
            self.add_failed_doc(uri, err)

    def add_pending_doc(
        self,
        uri: str,
    ):
        """Add a pending document report."""
        self.add_doc_report(DocumentReport(uri=uri, status=DocumentStatus.pending))

    def add_successful_doc(
        self,
        uri: str,
    ):
        """Add a successfully completed document report."""
        self.add_doc_report(DocumentReport(uri=uri, status=DocumentStatus.success))

    def add_failed_doc(
        self,
        uri: str,
        err: Exception,
    ):
        """Add a failed document report."""
        self.add_doc_report(
            DocumentReport(
                uri=uri,
                status=DocumentStatus.failure,
                details=DocumentStatusDetails(
                    error=err.__class__,
                    message=str(err),
                ),
            ),
        )

    def add_doc_report(
        self,
        report: DocumentReport,
    ):
        """Add a document report."""
        self._doc_reports[report.uri] = report

    def get_doc_report(
        self,
        uri: str,
    ):
        """Return a document report."""
        return self._doc_reports.get(uri)

    def _get_docs_by_status(
        self,
        status: DocumentStatus,
    ) -> list[str]:
        """Return documents' URIs having a specific status."""
        return [
            uri for uri, report in self._doc_reports.items() if report.status == status
        ]


class DocumentReport(BaseModel):
    """A class representing a document's report."""

    uri: str
    status: DocumentStatus
    details: DocumentStatusDetails = None


class DocumentStatus(Enum):
    """A document's status enum."""

    success: str = "SUCCESS"
    failure: str = "FAILURE"
    pending: str = "PENDING"


class DocumentStatusDetails(BaseModel):
    """A class representing a document's status details."""

    error: type
    message: str
