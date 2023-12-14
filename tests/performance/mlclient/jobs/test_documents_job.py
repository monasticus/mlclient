from __future__ import annotations

import pytest

from mlclient.clients import DocumentsClient
from mlclient.exceptions import MarkLogicError
from mlclient.jobs import WriteDocumentsJob
from mlclient.model import Document, DocumentType, RawDocument


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
    docs = list(_generate_docs(docs_count))
    uris = [doc.uri for doc in docs]

    try:
        _assert_documents_do_not_exist(uris)

        benchmark(_write_job_with_documents_input, docs, thread_count, batch_size)
        job = WriteDocumentsJob()
        job.with_client_config(auth_method="digest")
        job.with_documents_input(docs)
        job.start()
        job.await_completion()
        assert job.completed_count == docs_count
        assert len(job.successful) == docs_count
        assert len(job.failed) == 0

        _assert_documents_exist_and_confirm_data(
            {doc.uri: doc for doc in docs},
            output_type=bytes,
        )
    finally:
        _delete_documents(uris)
        _assert_documents_do_not_exist(uris)


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


def _generate_docs(
    count: int = 100,
):
    content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    for i in range(count):
        yield RawDocument(
            content=content,
            uri=f"/some/dir/doc{i+1}.xml",
            doc_type=DocumentType.XML,
        )


def _assert_documents_do_not_exist(
    uris: list,
):
    with DocumentsClient(auth_method="digest") as docs_client:
        assert docs_client.read(uris) == []


def _assert_documents_exist_and_confirm_data(
    expected: dict,
    category: str | list[str] = "content",
    output_type: type | None = None,
):
    with DocumentsClient(auth_method="digest") as docs_client:
        actual_docs = docs_client.read(
            list(expected.keys()),
            category,
            output_type=output_type,
        )
        for actual_doc in actual_docs:
            expected_doc = next(
                (doc for uri, doc in expected.items() if uri == actual_doc.uri),
                None,
            )
            assert expected_doc is not None
            assert actual_doc.uri == expected_doc.uri
            assert actual_doc.doc_type == expected_doc.doc_type
            if output_type is str:
                assert actual_doc.content == expected_doc.content_string
            elif output_type is bytes:
                assert actual_doc.content == expected_doc.content_bytes
            else:
                assert actual_doc.content_bytes == expected_doc.content_bytes
            if category not in ("content", ["content"]):
                assert actual_doc.metadata == expected_doc.metadata


def _delete_documents(
    uri: str | list[str],
):
    try:
        with DocumentsClient(auth_method="digest") as docs_client:
            docs_client.delete(uri)
    except MarkLogicError as err:
        pytest.fail(str(err))
