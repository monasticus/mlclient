import responses

from mlclient.jobs import WriteDocumentsJob
from mlclient.model import DocumentType, RawDocument
from tests.tools import MLResponseBuilder


@responses.activate
def test_basic_job():
    docs = _get_test_docs(5)

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(_get_test_response_body(5))
    builder.build_post()

    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) == 1


@responses.activate
def test_job_with_custom_database():
    docs = _get_test_docs(5)

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("database", "Documents")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(_get_test_response_body(5))
    builder.build_post()

    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.with_database("Documents")
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) == 1


@responses.activate
def test_multi_thread_job():
    docs = _get_test_docs(150)

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(_get_test_response_body(150))
    builder.build_post()

    job = WriteDocumentsJob(batch_size=5)
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) >= 30


def _get_test_docs(
    count: int,
):
    for i in range(count):
        uri = f"/some/dir/doc{i+1}.xml"
        content = b"<root><child>data</child></root>"
        yield RawDocument(content, uri, DocumentType.XML)


def _get_test_response_body(
    count: int,
) -> dict:
    return {
        "documents": [
            {
                "uri": f"/some/dir/doc{i+1}.xml",
                "mime-type": "application/xml",
                "category": ["metadata", "content"],
            }
            for i in range(count)
        ],
    }
