"""The ML Documents Jobs module.

It exports high-level class to perform bulk operations in a MarkLogic server:
    * WriteDocumentsJob
        An async job writing documents into a MarkLogic database.
    * ReadDocumentsJob
        An async job reading documents from a MarkLogic database.
    * DocumentsLoader
        A class parsing files into Documents.
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
import json
import logging
import os
import xml.etree.ElementTree as ElemTree
from collections.abc import Generator, Iterable
from copy import copy
from enum import Enum
from pathlib import Path

import aiofiles
from pydantic import BaseModel

from mlclient.clients import AsyncMLClient
from mlclient.mimetypes import Mimetypes
from mlclient.models import Document, DocumentType, Metadata
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
                if self._fs_output_path is not None:
                    kwargs["output_type"] = bytes
                for doc in await ml.documents.read_stream(batch, **kwargs):
                    self._report.add_successful_doc(doc.uri)
                    self._documents.append(doc)
            except Exception as err:
                self._report.add_failed_docs(batch, err)
                logger.exception(
                    "An unexpected error occurred while reading documents",
                )

    async def _save_documents(self):
        """Save read documents to the filesystem using aiofiles."""
        for doc in self._documents:
            await self._save_document(doc)

    async def _save_document(self, doc: Document):
        """Save a single document to the filesystem."""
        try:
            doc_path = self._fs_output_path / doc.uri[1:]
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            logger.fine("Writing data into file [%s]", doc_path)
            async with aiofiles.open(doc_path, mode="wb") as file:
                await file.write(doc.content_bytes)
            if doc.metadata is not None:
                metadata_path = doc_path.with_suffix(".metadata.json")
                logger.fine("Writing metadata into file [%s]", metadata_path)
                async with aiofiles.open(metadata_path, mode="wb") as file:
                    await file.write(doc.metadata)
        except Exception as err:
            self._report.add_failed_doc(doc.uri, err)


class DocumentsLoader:
    """A class parsing files into Documents."""

    _JSON_METADATA_SUFFIX = ".metadata.json"
    _XML_METADATA_SUFFIX = ".metadata.xml"
    _METADATA_SUFFIXES = (_JSON_METADATA_SUFFIX, _XML_METADATA_SUFFIX)

    @classmethod
    def load(
        cls,
        path: str,
        uri_prefix: str = "",
        raw: bool = True,
    ) -> Generator[Document]:
        """Load documents from files under a path.

        When the path points to a file - yields a single Document with URI set to
        the file name. Otherwise, yields documents with URIs without the input path
        at the beginning. Both option can be customized with the uri_prefix parameter.
        When the raw flag is true, all documents are parsed to RawDocument with bytes
        content and metadata.
        Metadata is identified for a file at the same level with .metadata.json or
        .metadata.xml suffix.

        Parameters
        ----------
        path : str
            A path to a directory or a single file.
        uri_prefix : str, default ""
            URIs prefix to apply
        raw : bool, default True
            A flag indicating whether files should be parsed to a RawDocument

        Returns
        -------
        Generator[Document]
            A generator of Document instances
        """
        if Path(path).is_file():
            file_path = path
            path = Path(path)
            uri = file_path.replace(str(path.parent), uri_prefix)
            yield cls.load_document(file_path, uri, raw)
        else:
            logger.debug("Loading documents from [%s] directory", path)
            for dir_path, _, file_names in os.walk(path):
                for file_name in file_names:
                    if file_name.endswith(cls._METADATA_SUFFIXES):
                        continue

                    file_path = str(Path(dir_path) / file_name)
                    uri = file_path.replace(path, uri_prefix)
                    yield cls.load_document(file_path, uri, raw)

    @classmethod
    def load_document(
        cls,
        path: str,
        uri: str | None = None,
        raw: bool = True,
    ) -> Document:
        """Load a document from a file.

        By default, returns a Document without URI. It can be customized with
        the uri parameter.
        When the raw flag is true, the document is parsed to RawDocument with bytes
        content and metadata.
        Metadata is identified for a file at the same level with .metadata.json or
        .metadata.xml suffix.

        Parameters
        ----------
        path : str
            A file path
        uri : str | None, default None
            URI to set for a document.
        raw : bool, default True
            A flag indicating whether file should be parsed to a RawDocument

        Returns
        -------
        Document
            A Document instance
        """
        doc_type = Mimetypes.get_doc_type(path)
        content = cls._load_content(path, raw, doc_type)
        metadata = cls._load_metadata(path, raw)

        factory_function = Document.create_raw if raw else Document.create

        return factory_function(
            content=content,
            doc_type=doc_type,
            uri=uri,
            metadata=metadata,
        )

    @classmethod
    def _load_content(
        cls,
        path: str,
        raw: bool,
        doc_type: DocumentType,
    ) -> bytes | str | ElemTree.Element | dict:
        """Load document's content.

        If the raw flag is switched off - it parses content based on a file type.
        Binary files are not being parsed, text files are parsed to str, xml files
        to ElementTree.Element and JSON files to a dict.

        Parameters
        ----------
        path : str
            A document path
        raw : bool, default True
            A flag indicating whether raw bytes should be returned
        doc_type : DocumentType
            A document type

        Returns
        -------
        bytes | str | ElemTree.Element | dict
            Document's content
        """
        with Path(path).open("rb") as file:
            content_bytes = file.read()

        if raw or doc_type == DocumentType.BINARY:
            return content_bytes
        if doc_type == DocumentType.TEXT:
            return content_bytes.decode("UTF-8")
        if doc_type == DocumentType.XML:
            return ElemTree.fromstring(content_bytes)
        return json.loads(content_bytes)

    @classmethod
    def _load_metadata(
        cls,
        path: str,
        raw: bool,
    ) -> bytes | Metadata | None:
        """Load document's metadata.

        It looks for a file with the same name and .metadata.json or .metadata.xml
        suffix and returns raw bytes or Metadata instance if found.

        Parameters
        ----------
        path : str
            A document path
        raw : bool, default True
            A flag indicating whether raw bytes should be returned

        Returns
        -------
        bytes | Metadata | None
            Document's metadata or None
        """
        metadata_paths = [
            Path(path).with_suffix(cls._JSON_METADATA_SUFFIX),
            Path(path).with_suffix(cls._XML_METADATA_SUFFIX),
        ]
        metadata_file_path = next(
            (str(path) for path in metadata_paths if path.is_file()),
            None,
        )
        if not metadata_file_path:
            return None

        logger.fine("Document [%s] loaded with metadata [%s]", path, metadata_file_path)
        if raw:
            with Path(metadata_file_path).open("rb") as metadata_file:
                return metadata_file.read()
        return Metadata.from_file(metadata_file_path)


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
