import xml.etree.ElementTree as ElemTree
import zlib

import pytest
import responses

from mlclient.calls.model import DocumentsBodyPart
from mlclient.clients import DocumentsClient
from mlclient.exceptions import MarkLogicError
from mlclient.model import (BinaryDocument, DocumentType, JSONDocument,
                            TextDocument, XMLDocument)
from tests.tools import MLResponseBuilder


@pytest.fixture(autouse=True)
def docs_client() -> DocumentsClient:
    return DocumentsClient(port=8000, auth_method="digest")


@pytest.fixture(autouse=True)
def _setup_and_teardown(docs_client):
    docs_client.connect()

    yield

    docs_client.disconnect()


@responses.activate
def test_read_non_existing_doc(docs_client):
    uri = "/some/dir/doc5.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc5.xml")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body({
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "RESTAPI-NODOCUMENT",
            "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
                       "Resource or document does not exist:  "
                       f"category: content message: {uri}",
        },
    })
    builder.build_get()
    with pytest.raises(MarkLogicError) as err:
        docs_client.read(uri)

    expected_error = ("[404 Not Found] (RESTAPI-NODOCUMENT) "
                      "RESTAPI-NODOCUMENT: (err:FOER0000) "
                      "Resource or document does not exist:  "
                      f"category: content message: {uri}")
    assert err.value.args[0] == expected_error


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

    document = docs_client.read(uri)

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is None
    assert document.is_temporal is False


@responses.activate
def test_read_xml_doc_using_uri_list(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/xml; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_body(b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
    builder.build_get()

    document = docs_client.read([uri])

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is None
    assert document.is_temporal is False


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

    document = docs_client.read(uri)

    assert isinstance(document, JSONDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.JSON
    assert isinstance(document.content, dict)
    assert document.content == {"root": {"child": "data"}}
    assert document.metadata is None
    assert document.is_temporal is False


@responses.activate
def test_read_json_doc_uri_list(docs_client):
    uri = "/some/dir/doc2.json"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(b'{"root":{"child":"data"}}')
    builder.build_get()

    document = docs_client.read([uri])

    assert isinstance(document, JSONDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.JSON
    assert isinstance(document.content, dict)
    assert document.content == {"root": {"child": "data"}}
    assert document.metadata is None
    assert document.is_temporal is False


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

    document = docs_client.read(uri)

    assert isinstance(document, TextDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.TEXT
    assert isinstance(document.content, str)
    assert document.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert document.metadata is None
    assert document.is_temporal is False


@responses.activate
def test_read_text_doc_uri_list(docs_client):
    uri = "/some/dir/doc3.xqy"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
    builder.with_response_status(200)
    builder.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
    builder.with_response_header("vnd.marklogic.document-format", "text")
    builder.build_get()

    document = docs_client.read([uri])

    assert isinstance(document, TextDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.TEXT
    assert isinstance(document.content, str)
    assert document.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert document.metadata is None
    assert document.is_temporal is False


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

    document = docs_client.read(uri)

    assert isinstance(document, BinaryDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.BINARY
    assert isinstance(document.content, bytes)
    assert document.content == content
    assert document.metadata is None
    assert document.is_temporal is False


@responses.activate
def test_read_binary_doc_uri_list(docs_client):
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

    document = docs_client.read([uri])

    assert isinstance(document, BinaryDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.BINARY
    assert isinstance(document.content, bytes)
    assert document.content == content
    assert document.metadata is None
    assert document.is_temporal is False


@responses.activate
def test_read_multiple_docs(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]
    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.json")
    builder.with_request_param("uri", "/some/dir/doc3.xqy")
    builder.with_request_param("uri", "/some/dir/doc4.zip")
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_documents_body_part(DocumentsBodyPart(**{
        "content-type": "application/zip",
        "content-disposition": 'attachment; '
                               'filename="/some/dir/doc4.zip"; '
                               'category=content; '
                               'format=binary',
        "content": zip_content}))
    builder.with_response_documents_body_part(DocumentsBodyPart(**{
        "content-type": "application/xml",
        "content-disposition": 'attachment; '
                               'filename="/some/dir/doc1.xml"; '
                               'category=content; '
                               'format=xml',
        "content": '<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<root><child>data</child></root>'}))
    builder.with_response_documents_body_part(DocumentsBodyPart(**{
        "content-type": "application/vnd.marklogic-xdmp",
        "content-disposition": 'attachment; '
                               'filename="/some/dir/doc3.xqy"; '
                               'category=content; '
                               'format=text',
        "content": 'xquery version "1.0-ml";\n\nfn:current-date()'}))
    builder.with_response_documents_body_part(DocumentsBodyPart(**{
        "content-type": "application/json",
        "content-disposition": 'attachment; '
                               'filename="/some/dir/doc2.json"; '
                               'category=content; '
                               'format=json',
        "content": {"root": {"child": "data"}}}))
    builder.build_get()

    docs = docs_client.read(uris)

    assert isinstance(docs, list)
    assert len(docs) == 4

    xml_docs = [doc for doc in docs if doc.uri.endswith(".xml")]
    assert len(xml_docs) == 1
    xml_doc = xml_docs[0]
    assert isinstance(xml_doc, XMLDocument)
    assert xml_doc.uri == "/some/dir/doc1.xml"
    assert xml_doc.doc_type == DocumentType.XML
    assert isinstance(xml_doc.content, ElemTree.ElementTree)
    assert xml_doc.content.getroot().tag == "root"
    assert xml_doc.content.getroot().text is None
    assert xml_doc.content.getroot().attrib == {}
    assert xml_doc.metadata is None
    assert xml_doc.is_temporal is False

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is None
    assert json_doc.is_temporal is False

    xqy_docs = list(filter(lambda d: d.uri.endswith(".xqy"), docs))
    assert len(xqy_docs) == 1
    xqy_doc = xqy_docs[0]
    assert isinstance(xqy_doc, TextDocument)
    assert xqy_doc.uri == "/some/dir/doc3.xqy"
    assert xqy_doc.doc_type == DocumentType.TEXT
    assert isinstance(xqy_doc.content, str)
    assert xqy_doc.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert xqy_doc.metadata is None
    assert xqy_doc.is_temporal is False

    zip_docs = list(filter(lambda d: d.uri.endswith(".zip"), docs))
    assert len(zip_docs) == 1
    zip_doc = zip_docs[0]
    assert isinstance(zip_doc, BinaryDocument)
    assert zip_doc.uri == "/some/dir/doc4.zip"
    assert zip_doc.doc_type == DocumentType.BINARY
    assert isinstance(zip_doc.content, bytes)
    assert zip_doc.content == zip_content
    assert zip_doc.metadata is None
    assert zip_doc.is_temporal is False


@responses.activate
def test_read_multiple_non_existing_docs(docs_client):
    uris = [
        "/some/dir/doc5.xml",
        "/some/dir/doc6.xml",
    ]

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc5.xml")
    builder.with_request_param("uri", "/some/dir/doc6.xml")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body({
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "RESTAPI-NODOCUMENT",
            "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
                       "Resource or document does not exist:  "
                       f"category: content message: {uris}",
        },
    })
    builder.build_get()
    with pytest.raises(MarkLogicError) as err:
        docs_client.read(uris)

    expected_error = ("[404 Not Found] (RESTAPI-NODOCUMENT) "
                      "RESTAPI-NODOCUMENT: (err:FOER0000) "
                      "Resource or document does not exist:  "
                      f"category: content message: {uris}")
    assert err.value.args[0] == expected_error


@responses.activate
def test_read_multiple_existing_and_non_existing_docs(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc5.xml",
        "/some/dir/doc6.json",
    ]
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.json")
    builder.with_request_param("uri", "/some/dir/doc5.xml")
    builder.with_request_param("uri", "/some/dir/doc6.json")
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_documents_body_part(DocumentsBodyPart(**{
        "content-type": "application/xml",
        "content-disposition": 'attachment; '
                               'filename="/some/dir/doc1.xml"; '
                               'category=content; '
                               'format=xml',
        "content": '<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<root><child>data</child></root>'}))
    builder.with_response_documents_body_part(DocumentsBodyPart(**{
        "content-type": "application/json",
        "content-disposition": 'attachment; '
                               'filename="/some/dir/doc2.json"; '
                               'category=content; '
                               'format=json',
        "content": {"root": {"child": "data"}}}))
    builder.build_get()

    docs = docs_client.read(uris)

    assert isinstance(docs, list)
    assert len(docs) == 2

    xml_docs = [doc for doc in docs if doc.uri.endswith(".xml")]
    assert len(xml_docs) == 1
    xml_doc = xml_docs[0]
    assert isinstance(xml_doc, XMLDocument)
    assert xml_doc.uri == "/some/dir/doc1.xml"
    assert xml_doc.doc_type == DocumentType.XML
    assert isinstance(xml_doc.content, ElemTree.ElementTree)
    assert xml_doc.content.getroot().tag == "root"
    assert xml_doc.content.getroot().text is None
    assert xml_doc.content.getroot().attrib == {}
    assert xml_doc.metadata is None
    assert xml_doc.is_temporal is False

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is None
    assert json_doc.is_temporal is False


@responses.activate
def test_read_doc_with_metadata(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8000/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_request_param("category", "content")
    builder.with_request_param("category", "metadata")
    builder.with_request_param("format", "json")
    builder.with_response_body_multipart_mixed()
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_documents_body_part(DocumentsBodyPart(**{
        "content-type": "application/json",
        "content-disposition": 'attachment; '
                               'filename="/some/dir/doc1.xml"; '
                               'category=metadata; '
                               'format=json',
        "content": {
            "collections": [],
            "permissions": [],
            "properties": {},
            "quality": 0,
            "metadataValues": {},
        }}))
    builder.with_response_documents_body_part(DocumentsBodyPart(**{
        "content-type": "application/xml",
        "content-disposition": 'attachment; '
                               'filename="/some/dir/doc1.xml"; '
                               'category=content; '
                               'format=xml',
        "content": '<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<root><child>data</child></root>'}))
    builder.build_get()

    document = docs_client.read(uri, category=["content", "metadata"])

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is not None
    assert document.metadata.collections() == []
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.is_temporal is False