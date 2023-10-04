import pytest
import responses

from mlclient.clients import DocumentsClient
from tests.tools import MLResponseBuilder
import xml.etree.ElementTree as ElemTree


@pytest.fixture(autouse=True)
def docs_client() -> DocumentsClient:
    return DocumentsClient(port=8000, auth_method="digest")


@pytest.fixture(autouse=True)
def _setup_and_teardown(docs_client):
    docs_client.connect()

    yield

    docs_client.disconnect()


@responses.activate
def test_read_xml_doc(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/xml; charset=utf-8")
    builder.with_response_status(200)
    builder.with_response_body('<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
    builder.build_get()

    resp = docs_client.read(uri)

    assert isinstance(resp, ElemTree.ElementTree)
    assert resp.getroot().tag == "root"
    assert resp.getroot().text is None
    assert resp.getroot().attrib == {}


@responses.activate
def test_read_json_doc(docs_client):
    uri = "/some/dir/doc2.json"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_status(200)
    builder.with_response_body('{"root":{"child":"data"}}')
    builder.build_get()

    resp = docs_client.read(uri)

    assert isinstance(resp, dict)
    assert resp == {"root": {"child": "data"}}
