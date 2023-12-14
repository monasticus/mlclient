"""The ML Documents Jobs module.

It exports high-level class to perform bulk operations in a MarkLogic server:
    * WriteDocumentsJob
        A multi-thread job writing documents into a MarkLogic database.
"""
from __future__ import annotations

import logging
import os
import queue
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from typing import Iterable

from mlclient.clients import DocumentsClient
from mlclient.model import Document

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
        self._input: list = []
        self._input_queue: queue.Queue = queue.Queue()
        self._executor: ThreadPoolExecutor | None = None
        self._successful = []
        self._failed = []

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

    def with_documents_input(
        self,
        documents: Iterable[Document],
    ):
        """Set the job's input in form of Documents' Iterable.

        Parameters
        ----------
        documents : Iterable[Document]
            Documents to be written into a MarkLogic database
        """
        Thread(
            target=self._populate_queue_with_documents_input,
            args=(self._input_queue, self._thread_count, documents),
        ).start()

    def start(
        self,
    ):
        """Start a job's execution."""
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

    @staticmethod
    def _populate_queue_with_documents_input(
        q: queue.Queue,
        thread_count: int,
        documents: Iterable[Document],
    ):
        """Populate a queue with Documents.

        It puts "poison pills" at the end of the queue to close each initialized thread.

        Parameters
        ----------
        q : queue.Queue
            A queue to populate
        thread_count : int
            A number of threads (to determine poison pills' number)
        documents : Iterable[Document]
            Documents to be written into a MarkLogic database
        """
        for document in documents:
            logger.debug("Putting [%s] into the queue", document.uri)
            q.put(document)
        for _ in range(thread_count):
            q.put(None)
