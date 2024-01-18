"""The ML Documents Jobs module.

It exports high-level class to perform bulk operations in a MarkLogic server:
    * WriteDocumentsJob
        A multi-thread job writing documents into a MarkLogic database.
"""
from __future__ import annotations

import json
import logging
import os
import queue
import uuid
import xml.etree.ElementTree as ElemTree
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Thread
from typing import Generator, Iterable

from mlclient.clients import DocumentsClient
from mlclient.mimetypes import Mimetypes
from mlclient.model import (
    Document,
    DocumentFactory,
    DocumentType,
    Metadata,
    MetadataFactory,
)

logger = logging.getLogger(__name__)


class WriteDocumentsJob:
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
        self._id: str = str(uuid.uuid4())
        self._thread_count: int = thread_count or self._get_max_num_of_threads()
        self._batch_size: int = batch_size
        self._config: dict = {}
        self._database: str | None = None
        self._pre_input_queue: queue.Queue = queue.Queue()
        self._input_queue: queue.Queue = queue.Queue()
        self._executor: ThreadPoolExecutor | None = None
        self._successful = []
        self._failed = []
        Thread(target=self._start_conveyor_belt).start()

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

    def with_filesystem_input(
        self,
        path: str,
        uri_prefix: str = "",
    ):
        """Load files under a directory and add parsed Documents to the job's input.

        Parameters
        ----------
        path : str
            An input directory with files to be written into a MarkLogic database
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

    def start(
        self,
    ):
        """Start a job's execution."""
        self._stop_conveyor_belt()

        logger.info("Starting job [%s]", self._id)
        self._executor = ThreadPoolExecutor(
            max_workers=self._thread_count,
            thread_name_prefix=f"write_documents_job_{self._id}",
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
    def completed_count(
        self,
    ) -> int:
        """A number of processed documents."""
        return len(self.completed)

    @property
    def completed(
        self,
    ) -> list[str]:
        """A list of processed documents."""
        completed = self.successful
        completed.extend(self.failed)
        return completed

    @property
    def successful(
        self,
    ) -> list[str]:
        """A list of successfully processed documents."""
        return list(self._successful)

    @property
    def failed(
        self,
    ) -> list[str]:
        """A list of processed documents that failed to be written."""
        return list(self._failed)

    def _start_conveyor_belt(
        self,
    ):
        """Populate an input queue with Documents in an infinitive loop.

        It is meant to be executed in a separated thread. Whenever any input
        is consumed it lends in a PRE-INPUT QUEUE first to allow for several inputs.
        Then it is moved to an INPUT QUEUE. Thanks to that we can be sure all data
        is placed before "poison pills". Once the job is started, there's no way
        to add anything else to process. It puts "poison pills" at the end
        of the INPUT QUEUE to close each initialized thread.
        """
        logger.info("Starting a conveyor belt for input documents")
        while True:
            documents = self._pre_input_queue.get()
            self._pre_input_queue.task_done()
            if documents is None:
                break

            for document in documents:
                logger.debug("Putting [%s] into the queue", document.uri)
                self._input_queue.put(document)

        for _ in range(self._thread_count):
            self._input_queue.put(None)

    def _stop_conveyor_belt(
        self,
    ):
        """Stop the infinitive loop populating an input queue with Documents."""
        logger.info("Stopping a conveyor belt for input documents")
        self._pre_input_queue.put(None)

    def _start(
        self,
    ):
        """Write documents in batches until queue is empty.

        Once DocumentsClient is initialized, it populates batches and writes them
        into a MarkLogicDatabase. When a batch size is lower than configured,
        the infinitive loop is stopped.
        """
        with DocumentsClient(**self._config) as client:
            while True:
                batch = self._populate_batch()
                if len(batch) > 0:
                    self._send_batch(batch, client)
                if len(batch) < self._batch_size:
                    logger.debug("No more documents in the queue. Closing a worker...")
                    break

    def _populate_batch(
        self,
    ) -> list[Document]:
        """Populate a documents' batch.

        Returns
        -------
        batch : list[Document]
            A batch with documents
        """
        batch = []
        for _ in range(self._batch_size):
            item = self._input_queue.get()
            self._input_queue.task_done()
            if item is None:
                break
            logger.debug("Getting [%s] from the queue", item.uri)
            batch.append(item)
        return batch

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
        try:
            client.create(data=batch, database=self._database)
            self._successful.extend([doc.uri for doc in batch])
        except Exception:
            self._failed.extend([doc.uri for doc in batch])
            logger.exception(
                "An unexpected error occurred while writing documents",
            )

    @staticmethod
    def _get_max_num_of_threads():
        """Get a maximum number of ThreadPoolExecutor workers."""
        return min(32, (os.cpu_count() or 1) + 4)  # Num of CPUs + 4


class DocumentsLoader:
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
        if Path(path).is_file():
            file_path = path
            path = Path(path)
            uri = file_path.replace(str(path.parent), uri_prefix)
            yield cls.load_document(file_path, uri, raw)
        else:
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
        file_path: str,
        uri: str | None = None,
        raw: bool = True,
    ) -> Document:
        doc_type = Mimetypes.get_doc_type(file_path)
        content = cls._load_content(file_path, raw, doc_type)
        metadata = cls._load_metadata(file_path, raw)

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
        file_path: str,
        raw: bool,
        doc_type: DocumentType,
    ) -> bytes | str | ElemTree.Element | dict:
        with Path(file_path).open("rb") as file:
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
        file_path: str,
        raw: bool,
    ) -> bytes | Metadata | None:
        metadata_paths = [
            Path(file_path).with_suffix(cls._JSON_METADATA_SUFFIX),
            Path(file_path).with_suffix(cls._XML_METADATA_SUFFIX),
        ]
        metadata_file_path = next(
            (str(path) for path in metadata_paths if path.is_file()),
            None,
        )
        if not metadata_file_path:
            return None

        if raw:
            with Path(metadata_file_path).open("rb") as metadata_file:
                return metadata_file.read()
        return MetadataFactory.from_file(metadata_file_path)
