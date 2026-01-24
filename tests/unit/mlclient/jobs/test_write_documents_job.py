import respx

from mlclient.exceptions import MarkLogicError
from mlclient.jobs import WriteDocumentsJob
from mlclient.structures import DocumentType, RawDocument
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLDocumentsMocker, MLRespXMocker

ml_doc_mocker = MLDocumentsMocker()

ml_mocker = MLRespXMocker(router_base_url="http://localhost:8002/v1/documents")
ml_mocker.with_side_effect(side_effect=ml_doc_mocker.post_documents_side_effect)
ml_mocker.mock_post()


@ml_mocker.router
def test_basic_job_with_documents_input():
    docs = _get_test_docs(5)

    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()

    assert ml_mocker.router.calls.call_count == 1
    assert ml_mocker.router.calls.last.request.url.params.get("database") is None
    assert job.report.completed == 5
    assert job.report.successful == 5
    assert job.report.failed == 0


@ml_mocker.router
def test_basic_job_with_filesystem_input():
    input_path = resources_utils.get_test_resources_path(__file__)
    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_filesystem_input(input_path, "/root/dir")
    job.start()
    job.await_completion()

    assert ml_mocker.router.calls.call_count == 1
    assert ml_mocker.router.calls.last.request.url.params.get("database") is None
    assert job.report.completed == 5
    assert job.report.successful == 5
    assert job.report.failed == 0


@ml_mocker.router
def test_basic_job_with_multiple_inputs():
    docs = list(_get_test_docs(5000))

    job = WriteDocumentsJob(thread_count=1, batch_size=50)
    assert job.thread_count == 1
    assert job.batch_size == 50
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs[:2500])
    job.with_documents_input(docs[2500:])
    job.start()
    job.await_completion()

    assert ml_mocker.router.calls.call_count == 100
    assert ml_mocker.router.calls.last.request.url.params.get("database") is None
    assert job.report.completed == 5000
    assert job.report.successful == 5000
    assert job.report.failed == 0


@ml_mocker.router
def test_job_with_custom_database():
    docs = _get_test_docs(5)

    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.with_database("Documents")
    job.start()
    job.await_completion()

    assert ml_mocker.router.calls.call_count == 1
    assert ml_mocker.router.calls.last.request.url.params.get("database") == "Documents"
    assert job.report.completed == 5
    assert job.report.successful == 5
    assert job.report.failed == 0


@ml_mocker.router
def test_multi_thread_job():
    docs = _get_test_docs(150)

    job = WriteDocumentsJob(batch_size=5)
    assert job.thread_count > 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()

    assert ml_mocker.router.calls.call_count >= 30
    assert ml_mocker.router.calls.last.request.url.params.get("database") is None
    assert job.report.completed == 150
    assert job.report.successful == 150
    assert job.report.failed == 0


@respx.mock
def test_failing_job():
    docs = _get_test_docs(5)

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8002/v1/documents")
    mocker.with_response_content_type("application/json; charset=utf-8")
    mocker.with_response_code(401)
    mocker.with_response_body(
        {
            "errorResponse": {
                "statusCode": 401,
                "status": "Unauthorized",
                "message": "401 Unauthorized",
            },
        },
    )
    mocker.mock_post()

    job = WriteDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config()
    job.with_documents_input(docs)
    job.start()
    job.await_completion()

    assert respx.calls.call_count == 1
    assert job.report.completed == 5
    assert job.report.successful == 0
    assert job.report.failed == 5
    for doc in docs:
        doc_report = job.report.get_doc_report(doc.uri)
        assert doc_report.details.error == MarkLogicError
        assert doc_report.details.message == "[401 Unauthorized] 401 Unauthorized"


def _get_test_docs(
    count: int,
):
    for i in range(count):
        uri = f"/some/dir/doc{i+1}.xml"
        content = b"<root><child>data</child></root>"
        yield RawDocument(content, uri, DocumentType.XML)
