"""The ML Documents Jobs module.

It exports high-level class to perform bulk operations in a MarkLogic server:
    * DocumentsJob
        An abstract class for jobs managing documents from a MarkLogic database.
    * WriteDocumentsJob
        A multi-thread job writing documents into a MarkLogic database.
    * ReadDocumentsJob
        A multi-thread job reading documents from a MarkLogic database.
    * DocumentsLoader
        A class parsing files into Documents.
    * DocumentJobReport
        A class representing a documents job report.
    * DocumentReport
        A class representing a document's report.
    * DocumentStatus
        A document's status enum.
    * DocumentReport
        A class representing a document's status details.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import uuid
import xml.etree.ElementTree as ElemTree
from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from copy import copy
from enum import Enum
from pathlib import Path
from threading import Thread
from typing import Generator, Iterable

import aiofiles
from pydantic import BaseModel

from mlclient.clients import DocumentsClient
from mlclient.mimetypes import Mimetypes
from mlclient.structures import (
    Document,
    DocumentFactory,
    DocumentType,
    Metadata,
    MetadataFactory,
)

logger = logging.getLogger(__name__)


class DocumentsJob(metaclass=ABCMeta):
    """An abstract class for jobs managing documents from a MarkLogic database."""

    def __init__(
        self,
        _type: str,
        thread_count: int | None = None,
        batch_size: int = 50,
    ):
        """Initialize a DocumentsJob instance.

        Parameters
        ----------
        thread_count : int | None, default None
            A number of threads
        batch_size : int, default 50
            A number of items in a single batch
        """
        self._type: str = _type
        self._id: str = str(uuid.uuid4())
        self._thread_count: int = thread_count or self._get_max_num_of_threads()
        self._batch_size: int = batch_size
        self._config: dict = {}
        self._database: str | None = None
        self._pre_input_queue: queue.Queue = queue.Queue()
        self._input_queue: queue.Queue = queue.Queue()
        self._executor: ThreadPoolExecutor | None = None
        self._report = DocumentJobReport()
        Thread(
            target=self._start_conveyor_belt,
            name=f"{self._type}_documents_job_{self._id}",
        ).start()

    def with_client_config(
        self,
        **config,
    ):
        """Set DocumentsClient configuration.

        Parameters
        ----------
        config
            Keyword arguments to be passed for a DocumentsClient instance.
        """
        self._config = config

    def with_database(
        self,
        database: str,
    ):
        """Set a database name.

        Parameters
        ----------
        database : str
            A database name
        """
        self._database = database

    def start(
        self,
    ):
        """Start a job's execution."""
        self._stop_conveyor_belt()

        logger.info("Starting job [%s]", self._id)
        self._executor = ThreadPoolExecutor(
            max_workers=self._thread_count,
            thread_name_prefix=f"{self._type}_documents_job_{self._id}",
        )

        for _ in range(self._thread_count):
            self._executor.submit(self._start)

    def await_completion(
        self,
    ):
        """Await a job's completion."""
        if not self._input_queue.empty():
            logger.info("Waiting for job [%s] completion", self._id)
        self._input_queue.join()
        self._executor.shutdown()
        self._executor = None
        logger.info(
            "Job [%s] has been completed "
            "with overall documents count [%d] and successful [%d]",
            self._id,
            self.report.completed,
            self.report.successful,
        )

    @property
    def thread_count(
        self,
    ) -> int:
        """A number of threads."""
        return self._thread_count

    @property
    def batch_size(
        self,
    ) -> int:
        """A number of documents in a single batch."""
        return self._batch_size

    @property
    def report(
        self,
    ) -> DocumentJobReport:
        """A status of the job."""
        return copy(self._report)

    def _start_conveyor_belt(
        self,
    ):
        """Populate an input queue with data in an infinitive loop.

        It is meant to be executed in a separated thread. Whenever any input
        is consumed it lends in a PRE-INPUT QUEUE first to allow for multiple inputs.
        Then it is moved to an INPUT QUEUE. Thanks to that we can be sure all data
        is placed before "poison pills". Once the job is started, there's no way
        to add anything else to process. It puts "poison pills" at the end
        of the INPUT QUEUE to terminate each initialized thread.
        """
        logger.info("Starting a conveyor belt for input data")
        while True:
            input_items = self._pre_input_queue.get()
            self._pre_input_queue.task_done()
            if input_items is None:
                break

            for input_item in input_items:
                uri = input_item.uri if isinstance(input_item, Document) else input_item
                logger.debug("Putting [%s] into the queue", uri)
                self._report.add_pending_doc(uri)
                self._input_queue.put(input_item)

        for _ in range(self._thread_count):
            self._input_queue.put(None)

    def _stop_conveyor_belt(
        self,
    ):
        """Stop the infinitive loop populating an input queue."""
        logger.info("Stopping a conveyor belt for input data")
        self._pre_input_queue.put(None)

    def _start(
        self,
    ):
        """Perform documents job in batches until queue is empty.

        Once DocumentsClient is initialized, it populates batches and sends requests
        against a MarkLogic server. When a batch size is lower than configured,
        the infinitive loop is stopped.
        """
        with DocumentsClient(**self._config) as client:
            while True:
                batch = self._populate_batch()
                if len(batch) > 0:
                    self._send_batch(batch, client)
                if len(batch) < self._batch_size:
                    logger.debug("No more data in the queue. Closing a worker...")
                    break

    def _populate_batch(
        self,
    ) -> list[str | Document]:
        """Populate a batch.

        Returns
        -------
        batch : list[str | Document]
            A batch with URIs or Documents
        """
        batch = []
        for _ in range(self._batch_size):
            item = self._input_queue.get()
            self._input_queue.task_done()
            if item is None:
                break
            logger.debug(
                "Getting [%s] from the queue",
                item.uri if isinstance(item, Document) else item,
            )
            batch.append(item)
        return batch

    @abstractmethod
    def _send_batch(
        self,
        batch: list[str],
        client: DocumentsClient,
    ):
        """Send a batch to /v1/documents endpoint."""
        raise NotImplementedError

    @staticmethod
    def _get_max_num_of_threads():
        """Get a maximum number of ThreadPoolExecutor workers."""
        return min(32, (os.cpu_count() or 1) + 4)  # Num of CPUs + 4


class ReadDocumentsJob(DocumentsJob):
    """A multi-thread job reading documents from a MarkLogic database."""

    def __init__(
        self,
        thread_count: int | None = None,
        batch_size: int = 400,
    ):
        """Initialize ReadDocumentsJob instance.

        Parameters
        ----------
        thread_count : int | None, default None
            A number of threads
        batch_size : int, default 300
            A number of URIs in a single batch
        """
        super().__init__("read", thread_count, batch_size)
        self._output_queue: queue.Queue = queue.Queue()
        self._categories: list[str] = ["content"]
        self._fs_output_path: Path | None = None
        self._fs_output_thread: Thread | None = None

    def start(
        self,
    ):
        """Start a job's execution."""
        if self._fs_output_path is not None:
            self._fs_output_thread = Thread(
                target=self._save_documents,
                name=f"{self._type}_documents_job_{self._id}_save",
            )
            self._fs_output_thread.start()
        super().start()

    def await_completion(
        self,
    ):
        """Await a job's completion."""
        super().await_completion()
        if self._fs_output_thread is not None:
            self._output_queue.put(None)
            self._fs_output_thread.join()

    def with_metadata(
        self,
        *args,
    ):
        """Add metadata category/ies to retrieve from a MarkLogic server.

        When no category is provided, full metadata will be gathered.

        Parameters
        ----------
        args :
            Metadata categories to be red from a MarkLogic server
        """
        if len(args) == 0:
            self._categories.append("metadata")
        else:
            self._categories.extend(args)

    def with_uris_input(
        self,
        uris: Iterable[str],
    ):
        """Add URIs to the job's input.

        Parameters
        ----------
        uris : Iterable[str]
            URIs to be red from a MarkLogic database
        """
        self._pre_input_queue.put(uris)

    def with_filesystem_output(
        self,
        output_path: str,
    ):
        """Set filesystem output directory to save documents inside.

        Parameters
        ----------
        output_path : str
            A directory path to save documents output
        """
        self._fs_output_path = Path(output_path).resolve().absolute()

    def get_documents(
        self,
    ) -> list[Document]:
        """Return all read documents from the job."""
        if self._executor is not None:
            self.await_completion()

        docs = []
        while not self._output_queue.empty():
            docs.append(self._output_queue.get())
        return docs

    def _send_batch(
        self,
        batch: list[str],
        client: DocumentsClient,
    ):
        """Send a URIs' batch to /v1/documents endpoint.

        Parameters
        ----------
        batch : list[str]
            A batch with documents
        client : DocumentsClient
            A DocumentsClient instance to call documents endpoint.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        try:
            kwargs = {
                "uris": batch,
                "database": self._database,
            }
            if self._categories != ["content"]:
                kwargs["category"] = list(dict.fromkeys(self._categories))
            if self._fs_output_path is not None:
                kwargs["output_type"] = bytes
            for doc in client.read(**kwargs):
                self._report.add_successful_doc(doc.uri)
                self._output_queue.put(doc)
        except Exception as err:
            self._report.add_failed_docs(batch, err)
            logger.exception("An unexpected error occurred while reading documents")

    def _save_documents(
        self,
    ):
        async def _save():
            while True:
                doc: Document = self._output_queue.get()
                if doc is None:
                    break

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

        asyncio.run(_save())


class WriteDocumentsJob(DocumentsJob):
    """A multi-thread job writing documents into a MarkLogic database."""

    def __init__(
        self,
        thread_count: int | None = None,
        batch_size: int = 50,
    ):
        """Initialize WriteDocumentsJob instance.

        Parameters
        ----------
        thread_count : int | None, default None
            A number of threads
        batch_size : int, default 50
            A number of documents in a single batch
        """
        super().__init__("write", thread_count, batch_size)

    def with_filesystem_input(
        self,
        path: str,
        uri_prefix: str = "",
    ):
        """Load files and add parsed Documents to the job's input.

        Parameters
        ----------
        path : str
            An input path with file(s) to be written into a MarkLogic database
        uri_prefix : str, default ""
            An URI prefix to be put before files' relative path
        """
        documents = DocumentsLoader.load(path, uri_prefix)
        self._pre_input_queue.put(documents)

    def with_documents_input(
        self,
        documents: Iterable[Document],
    ):
        """Add Documents to the job's input.

        Parameters
        ----------
        documents : Iterable[Document]
            Documents to be written into a MarkLogic database
        """
        self._pre_input_queue.put(documents)

    def _send_batch(
        self,
        batch: list[Document],
        client: DocumentsClient,
    ):
        """Send a documents' batch to /v1/documents endpoint.

        Parameters
        ----------
        batch : list[Document]
            A batch with documents
        client : DocumentsClient
            A DocumentsClient instance to call documents endpoint.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        batch_uris = [doc.uri for doc in batch]
        try:
            client.create(data=batch, database=self._database)
            self._report.add_successful_docs(batch_uris)
        except Exception as err:
            self._report.add_failed_docs(batch_uris, err)
            logger.exception("An unexpected error occurred while writing documents")


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

        if raw:
            factory_function = DocumentFactory.build_raw_document
        else:
            factory_function = DocumentFactory.build_document

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
        return MetadataFactory.from_file(metadata_file_path)


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
