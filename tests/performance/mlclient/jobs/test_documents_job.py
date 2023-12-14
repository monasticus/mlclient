from __future__ import annotations

from mlclient.jobs import WriteDocumentsJob
from mlclient.model import Document
from tests.utils import documents_client as docs_client_utils


def test_writing_thousand_docs_with_default_settings(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=1000)


def test_writing_thousand_docs_with_default_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=1000, batch_size=100)


def test_writing_thousand_docs_with_default_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=1000, batch_size=200)


def test_writing_thousand_docs_with_default_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=1000, batch_size=300)


def test_writing_thousand_docs_with_4_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=1000, thread_count=4)


def test_writing_thousand_docs_with_8_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=1000, thread_count=8)


def test_writing_thousand_docs_with_12_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=1000, thread_count=12)


def test_writing_thousand_docs_with_24_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=1000, thread_count=12)


def test_writing_thousand_docs_with_4_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=4,
        batch_size=100,
    )


def test_writing_thousand_docs_with_8_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=8,
        batch_size=100,
    )


def test_writing_thousand_docs_with_12_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=12,
        batch_size=100,
    )


def test_writing_thousand_docs_with_24_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=12,
        batch_size=100,
    )


def test_writing_thousand_docs_with_4_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=4,
        batch_size=200,
    )


def test_writing_thousand_docs_with_8_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=8,
        batch_size=200,
    )


def test_writing_thousand_docs_with_12_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=12,
        batch_size=200,
    )


def test_writing_thousand_docs_with_24_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=12,
        batch_size=200,
    )


def test_writing_thousand_docs_with_4_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=4,
        batch_size=300,
    )


def test_writing_thousand_docs_with_8_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=8,
        batch_size=300,
    )


def test_writing_thousand_docs_with_12_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=12,
        batch_size=300,
    )


def test_writing_thousand_docs_with_24_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=1000,
        thread_count=12,
        batch_size=300,
    )


def _perform_parametrized_test(
    benchmark,
    docs_count: int,
    thread_count: int | None = None,
    batch_size: int = 50,
):
    docs = list(docs_client_utils.generate_docs(docs_count))
    uris = [doc.uri for doc in docs]

    try:
        docs_client_utils.assert_documents_do_not_exist(uris)

        benchmark(_write_job_with_documents_input, docs, thread_count, batch_size)
        job = WriteDocumentsJob()
        job.with_client_config(auth_method="digest")
        job.with_documents_input(docs)
        job.start()
        job.await_completion()
        assert job.completed_count == docs_count
        assert len(job.successful) == docs_count
        assert len(job.failed) == 0

        docs_client_utils.assert_documents_exist_and_confirm_data(
            {doc.uri: doc for doc in docs},
            output_type=bytes,
        )
    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)


def _write_job_with_documents_input(
    docs: list[Document],
    thread_count: int | None,
    batch_size: int,
):
    job = WriteDocumentsJob(thread_count=thread_count, batch_size=batch_size)
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()

    return job
