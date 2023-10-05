import xml.etree.ElementTree as ElemTree
import zlib

import pytest
import responses

from mlclient.clients import DocumentsClient
from tests.tools import MLResponseBuilder


@pytest.fixture(autouse=True)
def docs_client() -> DocumentsClient:
    return DocumentsClient(port=8000)


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
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_body(b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
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
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(b'{"root":{"child":"data"}}')
    builder.build_get()

    resp = docs_client.read(uri)

    assert isinstance(resp, dict)
    assert resp == {"root": {"child": "data"}}


@responses.activate
def test_read_text_doc(docs_client):
    uri = "/some/dir/doc3.xqy"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
    builder.with_response_status(200)
    builder.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
    builder.with_response_header("vnd.marklogic.document-format", "text")
    builder.build_get()

    resp = docs_client.read(uri)

    assert isinstance(resp, str)
    assert resp == 'xquery version "1.0-ml";\n\nfn:current-date()'


@responses.activate
def test_read_binary_doc(docs_client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/zip")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.with_response_header("vnd.marklogic.document-format", "binary")
    builder.build_get()

    resp = docs_client.read(uri)

    assert isinstance(resp, bytes)
    assert resp == content
