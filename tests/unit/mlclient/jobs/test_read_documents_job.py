import responses

from mlclient.jobs import ReadDocumentsJob
from mlclient.structures import XMLDocument, DocumentType
from mlclient.structures.calls import DocumentsBodyPart
from tests.utils import MLResponseBuilder
import xml.etree.ElementTree as ElemTree


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
    for uri in uris:
        builder.with_request_param("uri", uri)
    builder.with_request_param("format", "json")
    builder.with_response_body_multipart_mixed()
    builder.with_response_status(200)
    for document_body_part in _get_test_response_body(len(uris)):
        builder.with_response_documents_body_part(document_body_part)
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
    assert job.status.completed == len(uris)
    assert job.status.successful == len(uris)
    assert job.status.failed == 0
    for i, uri in enumerate(uris):
        doc = next(doc for doc in docs if doc.uri == uri)
        assert isinstance(doc, XMLDocument)
        assert doc.uri == uri
        assert doc.doc_type == DocumentType.XML
        assert doc.metadata is None
        assert doc.temporal_collection is None
        assert isinstance(doc.content, ElemTree.ElementTree)
        assert doc.content.getroot().tag == "root"
        assert doc.content.getroot().attrib == {}
        children = list(doc.content.getroot())
        assert len(children) == 1
        assert children[0].tag == "child"
        assert children[0].text == f"data{i+1}"
        assert children[0].attrib == {}


def _get_test_response_body(
    count: int,
) -> dict:
    for i in range(count):
        yield DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                f'filename="/some/dir/doc{i+1}.xml"; '
                "category=content; "
                "format=xml",
                "content": '<?xml version="1.0" encoding="UTF-8"?>\n'
                f"<root><child>data{i+1}</child></root>",
            },
        )
