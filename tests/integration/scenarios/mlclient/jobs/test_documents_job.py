from __future__ import annotations

import json

from mlclient.jobs import ReadDocumentsJob, WriteDocumentsJob
from tests.utils import documents_client as docs_client_utils


def test_write_job_with_documents_input():
    docs = list(docs_client_utils.generate_docs())
    uris = [doc.uri for doc in docs]

    try:
        docs_client_utils.assert_documents_do_not_exist(uris)

        job = WriteDocumentsJob()
        job.with_client_config(auth_method="digest")
        job.with_documents_input(docs)
        job.start()
        job.await_completion()
        assert job.status.completed == len(uris)
        assert job.status.successful == len(uris)
        assert job.status.failed == 0

        docs_client_utils.assert_documents_exist_and_confirm_data(
            {doc.uri: doc for doc in docs},
            output_type=bytes,
        )
    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)


def test_read_job_with_uris_input():
    written_docs = list(docs_client_utils.generate_docs())
    uris = [doc.uri for doc in written_docs]

    try:
        # WRITE
        job = WriteDocumentsJob()
        job.with_client_config(auth_method="digest")
        job.with_documents_input(written_docs)
        job.start()
        job.await_completion()
        docs_client_utils.assert_documents_exist(uris)

        job = ReadDocumentsJob()
        job.with_client_config(auth_method="digest")
        job.with_uris_input(uris)
        job.start()
        read_docs = job.get_documents()
        for actual_doc in read_docs:
            expected_doc = next(
                doc for doc in written_docs if actual_doc.uri == doc.uri
            )
            assert expected_doc.doc_type == actual_doc.doc_type
            assert expected_doc.content_bytes == actual_doc.content_bytes
            assert expected_doc.metadata is None
            assert expected_doc.temporal_collection == actual_doc.temporal_collection
    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)


def test_read_job_with_uris_input_and_metadata():
    written_docs = list(docs_client_utils.generate_docs(with_metadata=True))
    uris = [doc.uri for doc in written_docs]

    try:
        # WRITE
        job = WriteDocumentsJob()
        job.with_client_config(auth_method="digest")
        job.with_documents_input(written_docs)
        job.start()
        job.await_completion()
        docs_client_utils.assert_documents_exist(uris)

        job = ReadDocumentsJob()
        job.with_client_config(auth_method="digest")
        job.with_uris_input(uris)
        job.with_metadata()
        job.start()
        read_docs = job.get_documents()
        for actual_doc in read_docs:
            expected_doc = next(
                doc for doc in written_docs if actual_doc.uri == doc.uri
            )
            expected_doc_metadata = json.loads(expected_doc.metadata)
            assert expected_doc.doc_type == actual_doc.doc_type
            assert expected_doc.content_bytes == actual_doc.content_bytes
            assert expected_doc_metadata == actual_doc.metadata.to_json()
            assert expected_doc.temporal_collection == actual_doc.temporal_collection
    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)
