import responses

from mlclient.jobs import WriteDocumentsJob
from mlclient.structures import DocumentType, RawDocument
from tests.utils import MLResponseBuilder
from tests.utils import resources as resources_utils


@responses.activate
def test_basic_job_with_documents_input():
    docs = _get_test_docs(5)

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(_get_test_response_body(5))
    builder.build_post()

    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == 5
    assert job.status.successful == 5
    assert job.status.failed == 0


@responses.activate
def test_basic_job_with_filesystem_input():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(_get_test_response_body(5))
    builder.build_post()

    input_path = resources_utils.get_test_resources_path(__file__)
    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_filesystem_input(input_path, "/root/dir")
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == 5
    assert job.status.successful == 5
    assert job.status.failed == 0


@responses.activate
def test_basic_job_with_several_inputs():
    docs = list(_get_test_docs(5000))

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(_get_test_response_body(5))
    builder.build_post()

    job = WriteDocumentsJob(thread_count=1, batch_size=50)
    assert job.thread_count == 1
    assert job.batch_size == 50
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs[:2500])
    job.with_documents_input(docs[2500:])
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) == 100
    assert job.status.completed == 5000
    assert job.status.successful == 5000
    assert job.status.failed == 0


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
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.with_database("Documents")
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == 5
    assert job.status.successful == 5
    assert job.status.failed == 0


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
    assert job.thread_count > 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) >= 30
    assert job.status.completed == 150
    assert job.status.successful == 150
    assert job.status.failed == 0


@responses.activate
def test_failing_job():
    docs = _get_test_docs(5)

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_status(401)
    builder.with_response_body(
        {
            "errorResponse": {
                "statusCode": 401,
                "status": "Unauthorized",
                "message": "401 Unauthorized",
            },
        },
    )
    builder.build_post()

    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config()
    job.with_documents_input(docs)
    job.start()
    job.await_completion()
    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == 5
    assert job.status.successful == 0
    assert job.status.failed == 5


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
