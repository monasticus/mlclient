from __future__ import annotations

import xml.etree.ElementTree as ElemTree
import zlib
from pathlib import Path

import pytest
import responses

from mlclient.clients import DocumentsClient
from mlclient.exceptions import MarkLogicError
from mlclient.structures import (
    BinaryDocument,
    DocumentType,
    JSONDocument,
    Metadata,
    MetadataDocument,
    RawDocument,
    RawStringDocument,
    TextDocument,
    XMLDocument,
)
from mlclient.structures.calls import DocumentsBodyPart
from tests.utils import MLResponseBuilder
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLDocumentsMocker, MLRespXMocker

DOC_BODY_PARTS = [
    DocumentsBodyPart(
        **{
            "content-type": "application/zip",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc4.zip"; '
            "category=content; "
            "format=binary",
            "content": zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()'),
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/xml",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc1.xml"; '
            "category=content; "
            "format=xml",
            "content": b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/vnd.marklogic-xdmp",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc3.xqy"; '
            "category=content; "
            "format=text",
            "content": b'xquery version "1.0-ml";\n\nfn:current-date()',
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc2.json"; '
            "category=content; "
            "format=json",
            "content": b'{"root":{"child":"data"}}',
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc1.xml"; '
            "category=metadata; "
            "format=json",
            "content": b"{"
            b'"collections": ["xml"], '
            b'"permissions": [], '
            b'"properties": {}, '
            b'"quality": 0, '
            b'"metadataValues": {}'
            b"}",
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc1.xml"; '
            "category=collections; "
            "format=json",
            "content": b'{"collections": ["xml"]}',
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc1.xml"; '
            "category=collections; "
            "category=quality; "
            "format=json",
            "content": b'{"collections": ["xml"], "quality": 0}',
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc1.xml"; '
            "category=metadata-values; "
            "category=collections; "
            "category=permissions; "
            "category=properties; "
            "category=quality; "
            "format=json",
            "content": b"{"
            b'"collections": ["xml"], '
            b'"permissions": [], '
            b'"properties": {}, '
            b'"quality": 0, '
            b'"metadataValues": {}'
            b"}",
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc2.json"; '
            "category=metadata; "
            "format=json",
            "content": b"{"
            b'"collections": ["json"], '
            b'"permissions": [], '
            b'"properties": {}, '
            b'"quality": 1, '
            b'"metadataValues": {}'
            b"}",
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc2.json"; '
            "category=collections; "
            "format=json",
            "content": b'{"collections": ["json"]}',
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc2.json"; '
            "category=collections; "
            "category=quality; "
            "format=json",
            "content": b'{"collections": ["json"], "quality": 1}',
        },
    ),
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc2.json"; '
            "category=collections; "
            "category=metadata-values; "
            "category=permissions; "
            "category=properties; "
            "category=quality; "
            "format=json",
            "content": b"{"
            b'"collections": ["json"], '
            b'"permissions": [], '
            b'"properties": {}, '
            b'"quality": 1, '
            b'"metadataValues": {}'
            b"}",
        },
    ),
]


ml_doc_mocker = MLDocumentsMocker(DOC_BODY_PARTS)

ml_mocker = MLRespXMocker(router_base_url="http://localhost:8002/v1/documents")
ml_mocker.with_side_effect(side_effect=ml_doc_mocker.get_documents_side_effect)
ml_mocker.mock_get()
ml_mocker.with_side_effect(side_effect=ml_doc_mocker.post_documents_side_effect)
ml_mocker.mock_post()


@pytest.fixture(autouse=True)
def docs_client() -> DocumentsClient:
    return DocumentsClient(port=8002, auth_method="digest")


@pytest.fixture(autouse=True)
def _setup_and_teardown(docs_client):
    docs_client.connect()

    yield

    docs_client.disconnect()


@ml_mocker.router
def test_read_non_existing_doc(docs_client):
    uri = "/some/dir/doc5.xml"

    with pytest.raises(MarkLogicError) as err:
        docs_client.read(uri)

    expected_error = (
        "[500 Internal Server Error] (RESTAPI-NODOCUMENT) "
        "RESTAPI-NODOCUMENT: (err:FOER0000) "
        "Resource or document does not exist:  "
        f"category: content message: {uri}"
    )
    assert err.value.args[0] == expected_error


@ml_mocker.router
def test_read_xml_doc(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri)

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_xml_doc_using_uri_list(docs_client):
    uri = "/some/dir/doc1.xml"

    docs = docs_client.read([uri])
    assert isinstance(docs, list)
    assert len(docs) == 1

    document = docs[0]
    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_json_doc(docs_client):
    uri = "/some/dir/doc2.json"

    document = docs_client.read(uri)

    assert isinstance(document, JSONDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.JSON
    assert isinstance(document.content, dict)
    assert document.content == {"root": {"child": "data"}}
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_json_doc_using_uri_list(docs_client):
    uri = "/some/dir/doc2.json"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(b'{"root":{"child":"data"}}')
    builder.build_get()

    docs = docs_client.read([uri])
    assert isinstance(docs, list)
    assert len(docs) == 1

    document = docs[0]
    assert isinstance(document, JSONDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.JSON
    assert isinstance(document.content, dict)
    assert document.content == {"root": {"child": "data"}}
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_text_doc(docs_client):
    uri = "/some/dir/doc3.xqy"

    document = docs_client.read(uri)

    assert isinstance(document, TextDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.TEXT
    assert isinstance(document.content, str)
    assert document.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_text_doc_using_uri_list(docs_client):
    uri = "/some/dir/doc3.xqy"

    docs = docs_client.read([uri])
    assert isinstance(docs, list)
    assert len(docs) == 1

    document = docs[0]
    assert isinstance(document, TextDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.TEXT
    assert isinstance(document.content, str)
    assert document.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_binary_doc(docs_client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    document = docs_client.read(uri)

    assert isinstance(document, BinaryDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.BINARY
    assert isinstance(document.content, bytes)
    assert document.content == content
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_binary_doc_using_uri_list(docs_client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    docs = docs_client.read([uri])
    assert isinstance(docs, list)
    assert len(docs) == 1

    document = docs[0]
    assert isinstance(document, BinaryDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.BINARY
    assert isinstance(document.content, bytes)
    assert document.content == content
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_doc_as_string(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri, output_type=str)

    assert isinstance(document, RawStringDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, str)
    assert document.content == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_doc_as_string_using_uri_list(docs_client):
    uri = "/some/dir/doc1.xml"

    docs = docs_client.read([uri], output_type=str)
    assert isinstance(docs, list)
    assert len(docs) == 1

    document = docs[0]
    assert isinstance(document, RawStringDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, str)
    assert document.content == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_doc_as_bytes(docs_client):
    uri = "/some/dir/doc2.json"

    document = docs_client.read(uri, output_type=bytes)

    assert isinstance(document, RawDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.JSON
    assert isinstance(document.content, bytes)
    assert document.content == b'{"root":{"child":"data"}}'
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_doc_as_bytes_using_uri_list(docs_client):
    uri = "/some/dir/doc2.json"

    docs = docs_client.read([uri], output_type=bytes)
    assert isinstance(docs, list)
    assert len(docs) == 1

    document = docs[0]
    assert isinstance(document, RawDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.JSON
    assert isinstance(document.content, bytes)
    assert document.content == b'{"root":{"child":"data"}}'
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_existing_and_non_existing_doc(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc5.xml",
    ]

    docs = docs_client.read(uris)
    assert isinstance(docs, list)
    assert len(docs) == 1

    document = docs[0]
    assert isinstance(document, XMLDocument)
    assert document.uri == "/some/dir/doc1.xml"
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

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
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is None
    assert json_doc.temporal_collection is None

    xqy_docs = list(filter(lambda d: d.uri.endswith(".xqy"), docs))
    assert len(xqy_docs) == 1
    xqy_doc = xqy_docs[0]
    assert isinstance(xqy_doc, TextDocument)
    assert xqy_doc.uri == "/some/dir/doc3.xqy"
    assert xqy_doc.doc_type == DocumentType.TEXT
    assert isinstance(xqy_doc.content, str)
    assert xqy_doc.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert xqy_doc.metadata is None
    assert xqy_doc.temporal_collection is None

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    zip_docs = list(filter(lambda d: d.uri.endswith(".zip"), docs))
    assert len(zip_docs) == 1
    zip_doc = zip_docs[0]
    assert isinstance(zip_doc, BinaryDocument)
    assert zip_doc.uri == "/some/dir/doc4.zip"
    assert zip_doc.doc_type == DocumentType.BINARY
    assert isinstance(zip_doc.content, bytes)
    assert zip_doc.content == zip_content
    assert zip_doc.metadata is None
    assert zip_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_as_string(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    docs = docs_client.read(uris, output_type=str)

    assert isinstance(docs, list)
    assert len(docs) == 4

    xml_docs = [doc for doc in docs if doc.uri.endswith(".xml")]
    assert len(xml_docs) == 1
    xml_doc = xml_docs[0]
    assert isinstance(xml_doc, RawStringDocument)
    assert xml_doc.uri == "/some/dir/doc1.xml"
    assert xml_doc.doc_type == DocumentType.XML
    assert isinstance(xml_doc.content, str)
    assert xml_doc.content == ('<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
    assert xml_doc.metadata is None
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, RawStringDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, str)
    assert json_doc.content == '{"root":{"child":"data"}}'
    assert json_doc.metadata is None
    assert json_doc.temporal_collection is None

    xqy_docs = list(filter(lambda d: d.uri.endswith(".xqy"), docs))
    assert len(xqy_docs) == 1
    xqy_doc = xqy_docs[0]
    assert isinstance(xqy_doc, RawStringDocument)
    assert xqy_doc.uri == "/some/dir/doc3.xqy"
    assert xqy_doc.doc_type == DocumentType.TEXT
    assert isinstance(xqy_doc.content, str)
    assert xqy_doc.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert xqy_doc.metadata is None
    assert xqy_doc.temporal_collection is None

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    zip_docs = list(filter(lambda d: d.uri.endswith(".zip"), docs))
    assert len(zip_docs) == 1
    zip_doc = zip_docs[0]
    assert isinstance(zip_doc, RawDocument)
    assert zip_doc.uri == "/some/dir/doc4.zip"
    assert zip_doc.doc_type == DocumentType.BINARY
    assert isinstance(zip_doc.content, bytes)
    assert zip_doc.content == zip_content
    assert zip_doc.metadata is None
    assert zip_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_as_bytes(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    docs = docs_client.read(uris, output_type=bytes)

    assert isinstance(docs, list)
    assert len(docs) == 4

    xml_docs = [doc for doc in docs if doc.uri.endswith(".xml")]
    assert len(xml_docs) == 1
    xml_doc = xml_docs[0]
    assert isinstance(xml_doc, RawDocument)
    assert xml_doc.uri == "/some/dir/doc1.xml"
    assert xml_doc.doc_type == DocumentType.XML
    assert isinstance(xml_doc.content, bytes)
    assert xml_doc.content == (b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
    assert xml_doc.metadata is None
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, RawDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, bytes)
    assert json_doc.content == b'{"root":{"child":"data"}}'
    assert json_doc.metadata is None
    assert json_doc.temporal_collection is None

    xqy_docs = list(filter(lambda d: d.uri.endswith(".xqy"), docs))
    assert len(xqy_docs) == 1
    xqy_doc = xqy_docs[0]
    assert isinstance(xqy_doc, RawDocument)
    assert xqy_doc.uri == "/some/dir/doc3.xqy"
    assert xqy_doc.doc_type == DocumentType.TEXT
    assert isinstance(xqy_doc.content, bytes)
    assert xqy_doc.content == b'xquery version "1.0-ml";\n\nfn:current-date()'
    assert xqy_doc.metadata is None
    assert xqy_doc.temporal_collection is None

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    zip_docs = list(filter(lambda d: d.uri.endswith(".zip"), docs))
    assert len(zip_docs) == 1
    zip_doc = zip_docs[0]
    assert isinstance(zip_doc, RawDocument)
    assert zip_doc.uri == "/some/dir/doc4.zip"
    assert zip_doc.doc_type == DocumentType.BINARY
    assert isinstance(zip_doc.content, bytes)
    assert zip_doc.content == zip_content
    assert zip_doc.metadata is None
    assert zip_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_non_existing_docs(docs_client):
    uris = [
        "/some/dir/doc5.xml",
        "/some/dir/doc6.xml",
    ]

    docs = docs_client.read(uris)

    assert docs == []


@ml_mocker.router
def test_read_multiple_existing_and_non_existing_docs(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc5.xml",
        "/some/dir/doc6.json",
    ]

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
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is None
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_doc_with_full_metadata(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri, category=["content", "metadata"])

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_doc_with_single_metadata_category(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri, category=["content", "collections"])

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_doc_with_two_metadata_categories(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri, category=["content", "collections", "quality"])

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_doc_with_all_metadata_categories(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(
        uri,
        category=[
            "content",
            "metadata-values",
            "collections",
            "permissions",
            "properties",
            "quality",
        ],
    )

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_full_metadata_without_content(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri, category=["metadata"])

    assert isinstance(document, MetadataDocument)
    assert document.uri == uri
    assert document.doc_type is None
    assert document.content is None
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_single_metadata_category_without_content(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri, category=["collections"])

    assert isinstance(document, MetadataDocument)
    assert document.uri == uri
    assert document.doc_type is None
    assert document.content is None
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_two_metadata_categories_without_content(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri, category=["collections", "quality"])

    assert isinstance(document, MetadataDocument)
    assert document.uri == uri
    assert document.doc_type is None
    assert document.content is None
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_all_metadata_categories_without_content(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(
        uri,
        category=[
            "metadata-values",
            "collections",
            "permissions",
            "properties",
            "quality",
        ],
    )

    assert isinstance(document, MetadataDocument)
    assert document.uri == uri
    assert document.doc_type is None
    assert document.content is None
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]
    assert document.metadata.metadata_values() == {}
    assert document.metadata.permissions() == []
    assert document.metadata.properties() == {}
    assert document.metadata.quality() == 0
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_with_full_metadata(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    docs = docs_client.read(uris, category=["content", "metadata"])

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
    assert xml_doc.metadata is not None
    assert xml_doc.metadata.collections() == ["xml"]
    assert xml_doc.metadata.metadata_values() == {}
    assert xml_doc.metadata.permissions() == []
    assert xml_doc.metadata.properties() == {}
    assert xml_doc.metadata.quality() == 0
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is not None
    assert json_doc.metadata.collections() == ["json"]
    assert json_doc.metadata.metadata_values() == {}
    assert json_doc.metadata.permissions() == []
    assert json_doc.metadata.properties() == {}
    assert json_doc.metadata.quality() == 1
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_with_single_metadata_category(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    docs = docs_client.read(uris, category=["content", "collections"])

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
    assert xml_doc.metadata is not None
    assert xml_doc.metadata.collections() == ["xml"]
    assert xml_doc.metadata.metadata_values() == {}
    assert xml_doc.metadata.permissions() == []
    assert xml_doc.metadata.properties() == {}
    assert xml_doc.metadata.quality() == 0
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is not None
    assert json_doc.metadata.collections() == ["json"]
    assert json_doc.metadata.metadata_values() == {}
    assert json_doc.metadata.permissions() == []
    assert json_doc.metadata.properties() == {}
    assert json_doc.metadata.quality() == 0
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_with_two_metadata_categories(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    docs = docs_client.read(uris, category=["content", "collections", "quality"])

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
    assert xml_doc.metadata is not None
    assert xml_doc.metadata.collections() == ["xml"]
    assert xml_doc.metadata.metadata_values() == {}
    assert xml_doc.metadata.permissions() == []
    assert xml_doc.metadata.properties() == {}
    assert xml_doc.metadata.quality() == 0
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is not None
    assert json_doc.metadata.collections() == ["json"]
    assert json_doc.metadata.metadata_values() == {}
    assert json_doc.metadata.permissions() == []
    assert json_doc.metadata.properties() == {}
    assert json_doc.metadata.quality() == 1
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_with_all_metadata_categories(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    docs = docs_client.read(
        uris,
        category=[
            "content",
            "metadata-values",
            "collections",
            "permissions",
            "properties",
            "quality",
        ],
    )

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
    assert xml_doc.metadata is not None
    assert xml_doc.metadata.collections() == ["xml"]
    assert xml_doc.metadata.metadata_values() == {}
    assert xml_doc.metadata.permissions() == []
    assert xml_doc.metadata.properties() == {}
    assert xml_doc.metadata.quality() == 0
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is not None
    assert json_doc.metadata.collections() == ["json"]
    assert json_doc.metadata.metadata_values() == {}
    assert json_doc.metadata.permissions() == []
    assert json_doc.metadata.properties() == {}
    assert json_doc.metadata.quality() == 1
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_full_metadata_without_content(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    docs = docs_client.read(uris, category=["metadata"])

    assert isinstance(docs, list)
    assert len(docs) == 2

    xml_docs = [doc for doc in docs if doc.uri.endswith(".xml")]
    assert len(xml_docs) == 1
    xml_doc = xml_docs[0]
    assert isinstance(xml_doc, MetadataDocument)
    assert xml_doc.uri == "/some/dir/doc1.xml"
    assert xml_doc.doc_type is None
    assert xml_doc.content is None
    assert xml_doc.metadata is not None
    assert xml_doc.metadata.collections() == ["xml"]
    assert xml_doc.metadata.metadata_values() == {}
    assert xml_doc.metadata.permissions() == []
    assert xml_doc.metadata.properties() == {}
    assert xml_doc.metadata.quality() == 0
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, MetadataDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type is None
    assert json_doc.content is None
    assert json_doc.metadata is not None
    assert json_doc.metadata.collections() == ["json"]
    assert json_doc.metadata.metadata_values() == {}
    assert json_doc.metadata.permissions() == []
    assert json_doc.metadata.properties() == {}
    assert json_doc.metadata.quality() == 1
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_single_metadata_category_without_content(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    docs = docs_client.read(uris, category=["collections"])

    assert isinstance(docs, list)
    assert len(docs) == 2

    xml_docs = [doc for doc in docs if doc.uri.endswith(".xml")]
    assert len(xml_docs) == 1
    xml_doc = xml_docs[0]
    assert isinstance(xml_doc, MetadataDocument)
    assert xml_doc.uri == "/some/dir/doc1.xml"
    assert xml_doc.doc_type is None
    assert xml_doc.content is None
    assert xml_doc.metadata is not None
    assert xml_doc.metadata.collections() == ["xml"]
    assert xml_doc.metadata.metadata_values() == {}
    assert xml_doc.metadata.permissions() == []
    assert xml_doc.metadata.properties() == {}
    assert xml_doc.metadata.quality() == 0
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, MetadataDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type is None
    assert json_doc.content is None
    assert json_doc.metadata is not None
    assert json_doc.metadata.collections() == ["json"]
    assert json_doc.metadata.metadata_values() == {}
    assert json_doc.metadata.permissions() == []
    assert json_doc.metadata.properties() == {}
    assert json_doc.metadata.quality() == 0
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_two_metadata_categories_without_content(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    docs = docs_client.read(uris, category=["collections", "quality"])

    assert isinstance(docs, list)
    assert len(docs) == 2

    xml_docs = [doc for doc in docs if doc.uri.endswith(".xml")]
    assert len(xml_docs) == 1
    xml_doc = xml_docs[0]
    assert isinstance(xml_doc, MetadataDocument)
    assert xml_doc.uri == "/some/dir/doc1.xml"
    assert xml_doc.doc_type is None
    assert xml_doc.content is None
    assert xml_doc.metadata is not None
    assert xml_doc.metadata.collections() == ["xml"]
    assert xml_doc.metadata.metadata_values() == {}
    assert xml_doc.metadata.permissions() == []
    assert xml_doc.metadata.properties() == {}
    assert xml_doc.metadata.quality() == 0
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, MetadataDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type is None
    assert json_doc.content is None
    assert json_doc.metadata is not None
    assert json_doc.metadata.collections() == ["json"]
    assert json_doc.metadata.metadata_values() == {}
    assert json_doc.metadata.permissions() == []
    assert json_doc.metadata.properties() == {}
    assert json_doc.metadata.quality() == 1
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_all_metadata_categories_without_content(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    docs = docs_client.read(
        uris,
        category=[
            "metadata-values",
            "collections",
            "permissions",
            "properties",
            "quality",
        ],
    )

    assert isinstance(docs, list)
    assert len(docs) == 2

    xml_docs = [doc for doc in docs if doc.uri.endswith(".xml")]
    assert len(xml_docs) == 1
    xml_doc = xml_docs[0]
    assert isinstance(xml_doc, MetadataDocument)
    assert xml_doc.uri == "/some/dir/doc1.xml"
    assert xml_doc.doc_type is None
    assert xml_doc.content is None
    assert xml_doc.metadata is not None
    assert xml_doc.metadata.collections() == ["xml"]
    assert xml_doc.metadata.metadata_values() == {}
    assert xml_doc.metadata.permissions() == []
    assert xml_doc.metadata.properties() == {}
    assert xml_doc.metadata.quality() == 0
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, MetadataDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type is None
    assert json_doc.content is None
    assert json_doc.metadata is not None
    assert json_doc.metadata.collections() == ["json"]
    assert json_doc.metadata.metadata_values() == {}
    assert json_doc.metadata.permissions() == []
    assert json_doc.metadata.properties() == {}
    assert json_doc.metadata.quality() == 1
    assert json_doc.temporal_collection is None


@ml_mocker.router
def test_read_single_doc_using_custom_database(docs_client):
    uri = "/some/dir/doc1.xml"

    document = docs_client.read(uri, database="Documents")

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.content.getroot().text is None
    assert document.content.getroot().attrib == {}
    assert document.metadata is None
    assert document.temporal_collection is None


@ml_mocker.router
def test_read_multiple_docs_using_custom_database(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    docs = docs_client.read(uris, database="Documents")

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
    assert xml_doc.temporal_collection is None

    json_docs = list(filter(lambda d: d.uri.endswith(".json"), docs))
    assert len(json_docs) == 1
    json_doc = json_docs[0]
    assert isinstance(json_doc, JSONDocument)
    assert json_doc.uri == "/some/dir/doc2.json"
    assert json_doc.doc_type == DocumentType.JSON
    assert isinstance(json_doc.content, dict)
    assert json_doc.content == {"root": {"child": "data"}}
    assert json_doc.metadata is None
    assert json_doc.temporal_collection is None

    xqy_docs = list(filter(lambda d: d.uri.endswith(".xqy"), docs))
    assert len(xqy_docs) == 1
    xqy_doc = xqy_docs[0]
    assert isinstance(xqy_doc, TextDocument)
    assert xqy_doc.uri == "/some/dir/doc3.xqy"
    assert xqy_doc.doc_type == DocumentType.TEXT
    assert isinstance(xqy_doc.content, str)
    assert xqy_doc.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert xqy_doc.metadata is None
    assert xqy_doc.temporal_collection is None

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    zip_docs = list(filter(lambda d: d.uri.endswith(".zip"), docs))
    assert len(zip_docs) == 1
    zip_doc = zip_docs[0]
    assert isinstance(zip_doc, BinaryDocument)
    assert zip_doc.uri == "/some/dir/doc4.zip"
    assert zip_doc.doc_type == DocumentType.BINARY
    assert isinstance(zip_doc.content, bytes)
    assert zip_doc.content == zip_content
    assert zip_doc.metadata is None
    assert zip_doc.temporal_collection is None


@ml_mocker.router
def test_create_raw_document(docs_client):
    uri = "/some/dir/doc1.xml"
    content = b"<root><child>data</child></root>"
    doc = RawDocument(content, uri, DocumentType.XML)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_raw_string_document(docs_client):
    uri = "/some/dir/doc2.json"
    content = '{"root":{"child":"data"}}'
    doc = RawStringDocument(content, uri, DocumentType.JSON)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/json"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_xml_document(docs_client):
    uri = "/some/dir/doc1.xml"
    content_str = "<root><child>data</child></root>"
    content = ElemTree.ElementTree(ElemTree.fromstring(content_str))
    doc = XMLDocument(content, uri)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_json_document(docs_client):
    uri = "/some/dir/doc2.json"
    content = {"root": {"child": "data"}}
    doc = JSONDocument(content, uri)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/json"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_text_document(docs_client):
    uri = "/some/dir/doc3.xqy"
    content = 'xquery version "1.0-ml";\n\nfn:current-date()'
    doc = TextDocument(content, uri)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/vnd.marklogic-xdmp"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_binary_document(docs_client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc = BinaryDocument(content, uri)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/zip"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_metadata_document_when_doc_exists(docs_client):
    uri = "/some/dir/doc1.xml"
    metadata = Metadata(collections=["test-collection"])
    doc = MetadataDocument(uri, metadata)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == ""
    assert documents[0]["category"] == ["metadata"]


@ml_mocker.router
def test_create_metadata_document_when_doc_does_not_exists(docs_client):
    # NON_EXISTING part makes it simulating an error
    uri = "/some/dir/NON_EXISTING-doc.xml"
    metadata = Metadata(collections=["test-collection"])
    doc = MetadataDocument(uri, metadata)

    with pytest.raises(MarkLogicError) as err:
        docs_client.create(doc)

    expected_error = (
        "[500 Internal Server Error] (XDMP-DOCNOTFOUND) XDMP-DOCNOTFOUND: "
        f'xdmp:document-set-collections("{uri}", "test-collection")'
        " -- Document not found"
    )
    assert err.value.args[0] == expected_error


@ml_mocker.router
def test_create_multiple_documents(docs_client):
    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content_str = "<root><child>data</child></root>"
    doc_1_content = ElemTree.ElementTree(ElemTree.fromstring(doc_1_content_str))
    doc_1 = XMLDocument(doc_1_content, doc_1_uri)

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = {"root": {"child": "data"}}
    doc_2 = JSONDocument(doc_2_content, doc_2_uri)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = 'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3 = TextDocument(doc_3_content, doc_3_uri)

    doc_4_uri = "/some/dir/doc4.zip"
    doc_4_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc_4 = BinaryDocument(doc_4_content, doc_4_uri)

    resp = docs_client.create([doc_1, doc_2, doc_3, doc_4])

    documents = resp["documents"]
    assert len(documents) == 4

    doc_1_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".xml")
    )
    assert doc_1_info["uri"] == doc_1_uri
    assert doc_1_info["mime-type"] == "application/xml"
    assert doc_1_info["category"] == ["metadata", "content"]

    doc_2_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".json")
    )
    assert doc_2_info["uri"] == doc_2_uri
    assert doc_2_info["mime-type"] == "application/json"
    assert doc_2_info["category"] == ["metadata", "content"]

    doc_3_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".xqy")
    )
    assert doc_3_info["uri"] == doc_3_uri
    assert doc_3_info["mime-type"] == "application/vnd.marklogic-xdmp"
    assert doc_3_info["category"] == ["metadata", "content"]

    doc_4_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".zip")
    )
    assert doc_4_info["uri"] == doc_4_uri
    assert doc_4_info["mime-type"] == "application/zip"
    assert doc_4_info["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_raw_document_with_metadata(docs_client):
    uri = "/some/dir/doc1.xml"
    content = b"<root><child>data</child></root>"
    metadata = b'{"collections": ["test-collection"]}'
    doc = RawDocument(content, uri, DocumentType.XML, metadata)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_raw_string_document_with_metadata(docs_client):
    uri = "/some/dir/doc1.xml"
    content = "<root><child>data</child></root>"
    metadata = '{"collections": ["test-collection"]}'
    doc = RawStringDocument(content, uri, DocumentType.XML, metadata)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_xml_document_with_metadata(docs_client):
    uri = "/some/dir/doc1.xml"
    content_str = "<root><child>data</child></root>"
    content = ElemTree.ElementTree(ElemTree.fromstring(content_str))
    metadata = Metadata(collections=["test-collection"])
    doc = XMLDocument(content, uri, metadata)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_json_document_with_metadata(docs_client):
    uri = "/some/dir/doc2.json"
    content = {"root": {"child": "data"}}
    metadata = Metadata(collections=["test-collection"])
    doc = JSONDocument(content, uri, metadata)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/json"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_text_document_with_metadata(docs_client):
    uri = "/some/dir/doc3.xqy"
    content = 'xquery version "1.0-ml";\n\nfn:current-date()'
    metadata = Metadata(collections=["test-collection"])
    doc = TextDocument(content, uri, metadata)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/vnd.marklogic-xdmp"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_binary_document_with_metadata(docs_client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    metadata = Metadata(collections=["test-collection"])
    doc = BinaryDocument(content, uri, metadata)

    resp = docs_client.create(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/zip"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_multiple_documents_with_metadata(docs_client):
    metadata = Metadata(collections=["test-collection"])

    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content_str = "<root><child>data</child></root>"
    doc_1_content = ElemTree.ElementTree(ElemTree.fromstring(doc_1_content_str))
    doc_1 = XMLDocument(doc_1_content, doc_1_uri, metadata)

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = {"root": {"child": "data"}}
    doc_2 = JSONDocument(doc_2_content, doc_2_uri, metadata)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = 'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3 = TextDocument(doc_3_content, doc_3_uri, metadata)

    doc_4_uri = "/some/dir/doc4.zip"
    doc_4_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc_4 = BinaryDocument(doc_4_content, doc_4_uri, metadata)

    resp = docs_client.create([doc_1, doc_2, doc_3, doc_4])

    documents = resp["documents"]
    assert len(documents) == 4

    doc_1_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".xml")
    )
    assert doc_1_info["uri"] == doc_1_uri
    assert doc_1_info["mime-type"] == "application/xml"
    assert doc_1_info["category"] == ["metadata", "content"]

    doc_2_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".json")
    )
    assert doc_2_info["uri"] == doc_2_uri
    assert doc_2_info["mime-type"] == "application/json"
    assert doc_2_info["category"] == ["metadata", "content"]

    doc_3_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".xqy")
    )
    assert doc_3_info["uri"] == doc_3_uri
    assert doc_3_info["mime-type"] == "application/vnd.marklogic-xdmp"
    assert doc_3_info["category"] == ["metadata", "content"]

    doc_4_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".zip")
    )
    assert doc_4_info["uri"] == doc_4_uri
    assert doc_4_info["mime-type"] == "application/zip"
    assert doc_4_info["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_single_document_with_default_metadata(docs_client):
    default_metadata = Metadata(collections=["test-collection"])

    uri = "/some/dir/doc1.xml"
    content = b"<root><child>data</child></root>"
    doc = RawDocument(content, uri, DocumentType.XML)

    resp = docs_client.create([default_metadata, doc])

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_multiple_documents_with_default_metadata(docs_client):
    default_metadata = Metadata(collections=["test-collection"])

    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content_str = "<root><child>data</child></root>"
    doc_1_content = ElemTree.ElementTree(ElemTree.fromstring(doc_1_content_str))
    doc_1 = XMLDocument(doc_1_content, doc_1_uri)

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = {"root": {"child": "data"}}
    doc_2 = JSONDocument(doc_2_content, doc_2_uri)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = 'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3 = TextDocument(doc_3_content, doc_3_uri)

    doc_4_uri = "/some/dir/doc4.zip"
    doc_4_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc_4 = BinaryDocument(doc_4_content, doc_4_uri)

    resp = docs_client.create([default_metadata, doc_1, doc_2, doc_3, doc_4])

    documents = resp["documents"]
    assert len(documents) == 4

    doc_1_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".xml")
    )
    assert doc_1_info["uri"] == doc_1_uri
    assert doc_1_info["mime-type"] == "application/xml"
    assert doc_1_info["category"] == ["metadata", "content"]

    doc_2_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".json")
    )
    assert doc_2_info["uri"] == doc_2_uri
    assert doc_2_info["mime-type"] == "application/json"
    assert doc_2_info["category"] == ["metadata", "content"]

    doc_3_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".xqy")
    )
    assert doc_3_info["uri"] == doc_3_uri
    assert doc_3_info["mime-type"] == "application/vnd.marklogic-xdmp"
    assert doc_3_info["category"] == ["metadata", "content"]

    doc_4_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".zip")
    )
    assert doc_4_info["uri"] == doc_4_uri
    assert doc_4_info["mime-type"] == "application/zip"
    assert doc_4_info["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_only_default_metadata(docs_client):
    default_metadata = Metadata(collections=["test-collection"])

    resp = docs_client.create(default_metadata)

    documents = resp["documents"]
    assert len(documents) == 0


@ml_mocker.router
def test_create_single_document_using_custom_database(docs_client):
    uri = "/some/dir/doc1.xml"
    content = b"<root><child>data</child></root>"
    doc = RawDocument(content, uri, DocumentType.XML)

    resp = docs_client.create(doc, database="Documents")

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"
    assert documents[0]["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_multiple_documents_using_custom_database(docs_client):
    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content_str = "<root><child>data</child></root>"
    doc_1_content = ElemTree.ElementTree(ElemTree.fromstring(doc_1_content_str))
    doc_1 = XMLDocument(doc_1_content, doc_1_uri)

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = {"root": {"child": "data"}}
    doc_2 = JSONDocument(doc_2_content, doc_2_uri)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = 'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3 = TextDocument(doc_3_content, doc_3_uri)

    doc_4_uri = "/some/dir/doc4.zip"
    doc_4_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc_4 = BinaryDocument(doc_4_content, doc_4_uri)

    resp = docs_client.create([doc_1, doc_2, doc_3, doc_4], database="Documents")

    documents = resp["documents"]
    assert len(documents) == 4

    doc_1_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".xml")
    )
    assert doc_1_info["uri"] == doc_1_uri
    assert doc_1_info["mime-type"] == "application/xml"
    assert doc_1_info["category"] == ["metadata", "content"]

    doc_2_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".json")
    )
    assert doc_2_info["uri"] == doc_2_uri
    assert doc_2_info["mime-type"] == "application/json"
    assert doc_2_info["category"] == ["metadata", "content"]

    doc_3_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".xqy")
    )
    assert doc_3_info["uri"] == doc_3_uri
    assert doc_3_info["mime-type"] == "application/vnd.marklogic-xdmp"
    assert doc_3_info["category"] == ["metadata", "content"]

    doc_4_info = next(
        doc_info for doc_info in documents if doc_info["uri"].endswith(".zip")
    )
    assert doc_4_info["uri"] == doc_4_uri
    assert doc_4_info["mime-type"] == "application/zip"
    assert doc_4_info["category"] == ["metadata", "content"]


@ml_mocker.router
def test_create_document_with_temporal_collection(docs_client):
    uri = "/some/dir/doc1.xml"
    content = "<root><child>data</child><systemStart/><systemEnd/></root>"
    doc = RawStringDocument(content, uri, DocumentType.XML)

    resp = docs_client.create(doc, temporal_collection="temporal-collection")

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"
    assert documents[0]["category"] == ["metadata", "content"]


@responses.activate
def test_delete_single_document(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    try:
        docs_client.delete(uri)
    except MarkLogicError as err:
        pytest.fail(str(err))


@responses.activate
def test_delete_multiple_documents(docs_client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    for uri in uris:
        builder.with_request_param("uri", uri)
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    try:
        docs_client.delete(uris)
    except MarkLogicError as err:
        pytest.fail(str(err))


@responses.activate
def test_delete_document_with_single_category(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("category", "collections")
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    try:
        docs_client.delete(uri, category="collections")
    except MarkLogicError as err:
        pytest.fail(str(err))


@responses.activate
def test_delete_document_with_multiple_categories(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("category", "properties")
    builder.with_request_param("category", "collections")
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    try:
        docs_client.delete(uri, category=["properties", "collections"])
    except MarkLogicError as err:
        pytest.fail(str(err))


@responses.activate
def test_delete_document_with_custom_database(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("database", "Documents")
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    try:
        docs_client.delete(uri, database="Documents")
    except MarkLogicError as err:
        pytest.fail(str(err))


@responses.activate
def test_delete_document_with_non_existing_database(docs_client):
    uri = "/some/dir/doc1.xml"

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-delete-document-with-non-existing-database.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("database", "Document")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    with pytest.raises(MarkLogicError) as err:
        docs_client.delete(uri, database="Document")

    expected_error = (
        "[404 Not Found] (XDMP-NOSUCHDB) XDMP-NOSUCHDB: No such database Document"
    )
    assert err.value.args[0] == expected_error


@responses.activate
def test_delete_document_with_temporal_collection(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("temporal-collection", "temporal-collection")
    builder.with_response_header(
        "x-marklogic-system-time",
        "2023-11-28T06:46:51.297376Z",
    )
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    try:
        docs_client.delete(uri, temporal_collection="temporal-collection")
    except MarkLogicError as err:
        pytest.fail(str(err))


@responses.activate
def test_delete_document_with_wipe_temporal(docs_client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("temporal-collection", "temporal-collection")
    builder.with_request_param("result", "wiped")
    builder.with_response_header(
        "x-marklogic-system-time",
        "2023-11-28T09:02:48.09751Z",
    )
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    try:
        docs_client.delete(
            uri,
            temporal_collection="temporal-collection",
            wipe_temporal=True,
        )
    except MarkLogicError as err:
        pytest.fail(str(err))
