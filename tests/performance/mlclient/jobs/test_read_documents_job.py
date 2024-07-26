from __future__ import annotations

import pytest

from mlclient.jobs import WriteDocumentsJob, ReadDocumentsJob
from tests.utils import documents_client as docs_client_utils

NUMBER_OF_DOCS = 1000


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    uri_prefix = "/performance-tests/read-documents-job"
    uri_template = f"{uri_prefix}/doc-{{}}.xml"
    uris = [uri_template.format(i + 1) for i in range(NUMBER_OF_DOCS)]

    try:
        docs_client_utils.assert_documents_do_not_exist(uris)
        _write_job_with_documents_input(NUMBER_OF_DOCS, uri_template)
        docs_client_utils.assert_documents_exist(uris)

        yield

    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)


def test_reading_docs_with_default_settings(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS)


def test_reading_docs_with_default_threads_batch_50(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=50)


def test_reading_docs_with_default_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=100)


def test_reading_docs_with_default_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=200)


def test_reading_docs_with_default_threads_batch_400(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=400)


def test_reading_docs_with_4_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, thread_count=4)


def test_reading_docs_with_8_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, thread_count=8)


def test_reading_docs_with_12_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, thread_count=12)


def test_reading_docs_with_24_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, thread_count=24)


def test_reading_docs_with_4_threads_batch_50(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=50,
    )


def test_reading_docs_with_8_threads_batch_50(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=50,
    )


def test_reading_docs_with_12_threads_batch_50(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=50,
    )


def test_reading_docs_with_24_threads_batch_50(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=50,
    )


def test_reading_docs_with_4_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=100,
    )


def test_reading_docs_with_8_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=100,
    )


def test_reading_docs_with_12_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=100,
    )


def test_reading_docs_with_24_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=100,
    )


def test_reading_docs_with_4_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=200,
    )


def test_reading_docs_with_8_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=200,
    )


def test_reading_docs_with_12_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=200,
    )


def test_reading_docs_with_24_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=200,
    )


def test_reading_docs_with_4_threads_batch_400(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=400,
    )


def test_reading_docs_with_8_threads_batch_400(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=400,
    )


def test_reading_docs_with_12_threads_batch_400(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=400,
    )


def test_reading_docs_with_24_threads_batch_400(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=400,
    )


def _perform_parametrized_test(
    benchmark,
    docs_count: int,
    thread_count: int | None = None,
    batch_size: int = 300,
):
    uri_prefix = "/performance-tests/read-documents-job"
    uri_template = f"{uri_prefix}/doc-{{}}.xml"
    uris = [uri_template.format(i + 1) for i in range(docs_count)]

    job = benchmark(
        _read_job_with_uris_input,
        uris,
        thread_count,
        batch_size,
    )

    assert job.status.completed == docs_count
    assert job.status.successful == docs_count
    assert job.status.failed == 0


def _write_job_with_documents_input(
    docs_count: int,
    uri_template: str,
):
    docs = docs_client_utils.generate_docs(docs_count, uri_template=uri_template)
    job = WriteDocumentsJob()
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()


def _read_job_with_uris_input(
    uris: list[str],
    thread_count: int | None,
    batch_size: int,
):
    job = ReadDocumentsJob(thread_count=thread_count, batch_size=batch_size)
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.start()
    job.await_completion()

    return job
