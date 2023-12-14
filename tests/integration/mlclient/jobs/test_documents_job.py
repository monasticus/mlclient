from __future__ import annotations

from mlclient.jobs import WriteDocumentsJob
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
        assert job.completed_count == 100
        assert len(job.successful) == 100
        assert len(job.failed) == 0

        docs_client_utils.assert_documents_exist_and_confirm_data(
            {doc.uri: doc for doc in docs},
            output_type=bytes,
        )
    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)
