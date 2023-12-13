from __future__ import annotations

import logging
import os
import queue
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from typing import Iterator

from mlclient.clients import DocumentsClient
from mlclient.model import Document

logger = logging.getLogger(__name__)


class WriteDocumentsJob:
    def __init__(
        self,
        thread_count: int | None = None,
        batch_size: int = 50,
    ):
        self._id: str = str(uuid.uuid4())
        self._thread_count: int = thread_count or self._get_max_num_of_threads()
        self._batch_size: int = batch_size
        self._config: dict = {}
        self._database: str | None = None
        self._input: list = []
        self._input_queue: queue.Queue = queue.Queue()
        self._executor: ThreadPoolExecutor | None = None

    def with_client_config(
        self,
        **config,
    ):
        self._config = config

    def with_database(
        self,
        database: str,
    ):
        self._database = database

    def with_documents_input(
        self,
        documents: list[Document] | Iterator[Document],
    ):
        Thread(
            target=self._populate_queue_with_documents_input,
            args=(self._input_queue, self._thread_count, documents),
        ).start()

    def start(
        self,
    ):
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
        if not self._input_queue.empty():
            logger.info("Waiting for job [%s] completion", self._id)
        self._input_queue.join()
        self._executor.shutdown()
        self._executor = None

    def _start(
        self,
    ):
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
    ) -> list:
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
        batch: list,
        client: DocumentsClient,
    ):
        try:
            client.create(data=batch, database=self._database)
        except Exception:
            logger.exception(
                "An unexpected error occurred while writing documents",
            )

    @staticmethod
    def _get_max_num_of_threads():
        return min(32, (os.cpu_count() or 1) + 4)  # Num of CPUs + 4

    @staticmethod
    def _populate_queue_with_documents_input(
        q: queue.Queue,
        thread_count: int,
        documents: list[Document] | Iterator[Document],
    ):
        for document in documents:
            logger.debug("Putting [%s] into the queue", document.uri)
            q.put(document)
        for _ in range(thread_count):
            q.put(None)
