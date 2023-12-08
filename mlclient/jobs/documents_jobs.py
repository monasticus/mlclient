from __future__ import annotations

import os
import queue
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from typing import Iterator

from mlclient.clients import DocumentsClient
from mlclient.model import Document


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
        self._executor = ThreadPoolExecutor(
            max_workers=self._thread_count,
            thread_name_prefix=f"write_documents_job_{self._id}",
        )

        for _ in range(self._thread_count):
            self._executor.submit(self._start)

    def wait_completion(
        self,
    ):
        self._input_queue.join()
        self._executor.shutdown()
        self._executor = None

    @staticmethod
    def _populate_queue_with_documents_input(
        q,
        thread_count,
        documents: list[Document] | Iterator[Document],
    ):
        for document in documents:
            print(f"Putting {document.uri} to queue")
            q.put(document)
        for _ in range(thread_count):
            q.put(None)

    def _start(
        self,
    ):
        with DocumentsClient(**self._config) as client:
            while True:
                batch = []
                for _ in range(self._batch_size):
                    item = self._input_queue.get()
                    self._input_queue.task_done()
                    if item is None:
                        print("Getting None from queue")
                        break
                    print(f"Getting {item.uri} from queue")
                    batch.append(item)
                if len(batch) > 0:
                    try:
                        client.create(data=batch, database=self._database)
                    except Exception as err:
                        print(
                            f"An unexpected error occurred while writing documents: {err}",
                        )

                if len(batch) < self._batch_size:
                    print(f"Closing worker, batch {len(batch)}")
                    break

    @staticmethod
    def _get_max_num_of_threads():
        return min(32, (os.cpu_count() or 1) + 4)  # Num of CPUs + 4
