import responses

from mlclient.jobs import ReadDocumentsJob
from mlclient.structures.calls import DocumentsBodyPart
from tests.utils import MLResponseBuilder


@responses.activate
def test_basic_job():
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.xml",
        "/some/dir/doc3.xml",
        "/some/dir/doc4.xml",
        "/some/dir/doc5.xml",
    ]

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.xml")
    builder.with_request_param("uri", "/some/dir/doc3.xml")
    builder.with_request_param("uri", "/some/dir/doc4.xml")
    builder.with_request_param("uri", "/some/dir/doc5.xml")
    builder.with_request_param("format", "json")
    builder.with_response_body_multipart_mixed()
    builder.with_response_status(200)
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data1</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data2</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data3</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data4</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data5</child></root>",
            },
        ),
    )
    builder.build_get()

    job = ReadDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.start()
    docs = job.get_documents()
    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == 5
    assert job.status.successful == 5
    assert job.status.failed == 0
