from __future__ import annotations

from pathlib import Path

from mlclient.jobs import ReadDocumentsJob, WriteDocumentsJob
from tests.utils import documents_client as docs_client_utils
from tests.utils import filesystem as fs_utils


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
        assert job.report.completed == len(uris)
        assert job.report.successful == len(uris)
        assert job.report.failed == 0

        docs_client_utils.assert_documents_exist_and_confirm_data(
            {doc.uri: doc for doc in docs},
            output_type=bytes,
        )
    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)


def test_read_job_with_documents_output():
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


def test_read_job_with_filesystem_output():
    written_docs = list(docs_client_utils.generate_docs())
    uris = [doc.uri for doc in written_docs]

    output_dir = str(Path(__file__).resolve().parent / "output")
    assert not Path(output_dir).exists()
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
        job.with_filesystem_output(output_dir)
        job.start()
        job.await_completion()
        assert Path(output_dir).exists()
        assert len([p for p in Path(output_dir).rglob("*") if p.is_file()]) == len(uris)
        for uri in uris:
            expected_doc = next(doc for doc in written_docs if uri == doc.uri)
            file_path = Path(output_dir) / uri[1:]
            assert file_path.exists()
            with file_path.open("rb") as file:
                assert expected_doc.content_bytes == file.read()
    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)
        fs_utils.safe_rmdir(output_dir)
        assert not Path(output_dir).exists()
