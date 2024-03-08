import io
import xml.etree.ElementTree as ElemTree
import zipfile
from types import GeneratorType

from mlclient.jobs import DocumentsLoader
from mlclient.structures import (
    BinaryDocument,
    Document,
    DocumentType,
    JSONDocument,
    Metadata,
    RawDocument,
    TextDocument,
    XMLDocument,
)
from tests.utils import resources as resources_utils

TEST_RESOURCES_PATH = resources_utils.get_test_resources_path(__file__)


def test_load_documents():
    path = f"{TEST_RESOURCES_PATH}/root-1"

    docs = DocumentsLoader.load(path)
    assert type(docs) is GeneratorType

    docs = list(docs)
    assert len(docs) == 4

    doc_1 = next((doc for doc in docs if doc.uri == "/dir/doc-1.xml"), None)
    assert doc_1 is not None
    assert type(doc_1) is RawDocument
    assert doc_1.doc_type == DocumentType.XML
    assert doc_1.content == b"<root><parent><child>value-1</child></parent></root>"
    assert doc_1.metadata is None
    assert doc_1.temporal_collection is None

    doc_2 = next((doc for doc in docs if doc.uri == "/dir/doc-2.json"), None)
    assert doc_2 is not None
    assert type(doc_2) is RawDocument
    assert doc_2.doc_type == DocumentType.JSON
    assert doc_2.content == b'{"root": {"parent": {"child": "value-2"}}}'
    assert doc_2.metadata is None
    assert doc_2.temporal_collection is None

    doc_3 = next((doc for doc in docs if doc.uri == "/dir/doc-3.xqy"), None)
    assert doc_3 is not None
    assert type(doc_3) is RawDocument
    assert doc_3.doc_type == DocumentType.TEXT
    assert doc_3.content == b'xquery version "1.0-ml";\n\nfn:current-date()'
    assert doc_3.metadata is None
    assert doc_3.temporal_collection is None

    doc_4 = next((doc for doc in docs if doc.uri == "/dir/doc-4.zip"), None)
    assert doc_4 is not None
    assert type(doc_4) is RawDocument
    assert doc_4.doc_type == DocumentType.BINARY
    with zipfile.ZipFile(io.BytesIO(doc_4.content)) as zip_file:
        assert zip_file.namelist() == ["doc-3.xqy"]
        with zip_file.open("doc-3.xqy") as xqy_file:
            assert xqy_file.read() == doc_3.content
    assert doc_4.metadata is None
    assert doc_4.temporal_collection is None


def test_load_documents_with_metadata():
    path = f"{TEST_RESOURCES_PATH}/root-2"

    docs = DocumentsLoader.load(path)
    assert type(docs) is GeneratorType

    docs = list(docs)
    assert len(docs) == 7

    doc_1 = next((doc for doc in docs if doc.uri == "/dir/doc-1.xml"), None)
    assert doc_1 is not None
    assert type(doc_1) is RawDocument
    assert doc_1.doc_type == DocumentType.XML
    assert doc_1.content == b"<root><parent><child>value-1</child></parent></root>"
    assert doc_1.metadata is None
    assert doc_1.temporal_collection is None

    doc_2 = next((doc for doc in docs if doc.uri == "/dir/doc-2.json"), None)
    assert doc_2 is not None
    assert type(doc_2) is RawDocument
    assert doc_2.doc_type == DocumentType.JSON
    assert doc_2.content == b'{"root": {"parent": {"child": "value-2"}}}'
    assert doc_2.metadata == b'{"collections": ["json-doc-2"]}'
    assert doc_2.temporal_collection is None

    doc_3 = next((doc for doc in docs if doc.uri == "/dir/doc-3.xml"), None)
    assert doc_3 is not None
    assert type(doc_3) is RawDocument
    assert doc_3.doc_type == DocumentType.XML
    assert doc_3.content == b"<root><parent><child>value-3</child></parent></root>"
    assert doc_3.metadata == (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">\n'
        b"    <rapi:collections>\n"
        b"        <rapi:collection>xml-doc-3</rapi:collection>\n"
        b"    </rapi:collections>\n"
        b"</rapi:metadata>"
    )
    assert doc_3.temporal_collection is None

    doc_4 = next((doc for doc in docs if doc.uri == "/dir/doc-4.json"), None)
    assert doc_4 is not None
    assert type(doc_4) is RawDocument
    assert doc_4.doc_type == DocumentType.JSON
    assert doc_4.content == b'{"root": {"parent": {"child": "value-4"}}}'
    assert doc_4.metadata == (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">\n'
        b"    <rapi:collections>\n"
        b"        <rapi:collection>json-doc-4</rapi:collection>\n"
        b"    </rapi:collections>\n"
        b"</rapi:metadata>"
    )
    assert doc_4.temporal_collection is None

    doc_5 = next((doc for doc in docs if doc.uri == "/dir/doc-5.xml"), None)
    assert doc_5 is not None
    assert type(doc_5) is RawDocument
    assert doc_5.doc_type == DocumentType.XML
    assert doc_5.content == b"<root><parent><child>value-5</child></parent></root>"
    assert doc_5.metadata == b'{"collections": ["xml-doc-5"]}'
    assert doc_5.temporal_collection is None

    doc_6 = next((doc for doc in docs if doc.uri == "/dir/doc-6.json"), None)
    assert doc_6 is not None
    assert type(doc_6) is RawDocument
    assert doc_6.doc_type == DocumentType.JSON
    assert doc_6.content == b'{"root": {"parent": {"child": "value-6"}}}'
    assert doc_6.metadata == b'{"collections": ["json-doc-6-json-metadata"]}'
    assert doc_6.temporal_collection is None

    doc_7 = next((doc for doc in docs if doc.uri == "/dir/doc-7.xml"), None)
    assert doc_7 is not None
    assert type(doc_7) is RawDocument
    assert doc_7.doc_type == DocumentType.XML
    assert doc_7.content == b"<root><parent><child>value-7</child></parent></root>"
    assert doc_7.metadata == b'{"collections": ["xml-doc-7-json-metadata"]}'
    assert doc_7.temporal_collection is None


def test_load_documents_with_custom_uri_prefix():
    path = f"{TEST_RESOURCES_PATH}/root-1"

    docs = DocumentsLoader.load(path, uri_prefix="/custom-root")
    assert type(docs) is GeneratorType

    docs = list(docs)
    assert len(docs) == 4

    doc_1 = next((doc for doc in docs if doc.uri == "/dir/doc-1.xml"), None)
    assert doc_1 is None
    doc_1 = next((doc for doc in docs if doc.uri == "/custom-root/dir/doc-1.xml"), None)
    assert doc_1 is not None

    doc_2 = next((doc for doc in docs if doc.uri == "/dir/doc-2.json"), None)
    assert doc_2 is None
    doc_2 = next(
        (doc for doc in docs if doc.uri == "/custom-root/dir/doc-2.json"),
        None,
    )
    assert doc_2 is not None

    doc_3 = next((doc for doc in docs if doc.uri == "/dir/doc-3.xqy"), None)
    assert doc_3 is None
    doc_3 = next((doc for doc in docs if doc.uri == "/custom-root/dir/doc-3.xqy"), None)
    assert doc_3 is not None

    doc_4 = next((doc for doc in docs if doc.uri == "/dir/doc-4.zip"), None)
    assert doc_4 is None
    doc_4 = next(
        (doc for doc in docs if doc.uri == "/custom-root/dir/doc-4.zip"),
        None,
    )
    assert doc_4 is not None


def test_load_documents_and_parse():
    path = f"{TEST_RESOURCES_PATH}"

    docs = DocumentsLoader.load(path, raw=False)
    assert type(docs) is GeneratorType

    docs = list(docs)
    assert len(docs) == 11

    doc_1_1 = next((doc for doc in docs if doc.uri == "/root-1/dir/doc-1.xml"), None)
    assert doc_1_1 is not None
    assert type(doc_1_1) is XMLDocument
    assert doc_1_1.doc_type == DocumentType.XML
    _assert_xml_content_with_value(doc_1_1, "value-1")
    assert doc_1_1.metadata is None
    assert doc_1_1.temporal_collection is None

    doc_1_2 = next((doc for doc in docs if doc.uri == "/root-1/dir/doc-2.json"), None)
    assert doc_1_2 is not None
    assert type(doc_1_2) is JSONDocument
    assert doc_1_2.doc_type == DocumentType.JSON
    assert doc_1_2.content == {"root": {"parent": {"child": "value-2"}}}
    assert doc_1_2.metadata is None
    assert doc_1_2.temporal_collection is None

    doc_1_3 = next((doc for doc in docs if doc.uri == "/root-1/dir/doc-3.xqy"), None)
    assert doc_1_3 is not None
    assert type(doc_1_3) is TextDocument
    assert doc_1_3.doc_type == DocumentType.TEXT
    assert doc_1_3.content == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert doc_1_3.metadata is None
    assert doc_1_3.temporal_collection is None

    doc_1_4 = next((doc for doc in docs if doc.uri == "/root-1/dir/doc-4.zip"), None)
    assert doc_1_4 is not None
    assert type(doc_1_4) is BinaryDocument
    assert doc_1_4.doc_type == DocumentType.BINARY
    with zipfile.ZipFile(io.BytesIO(doc_1_4.content)) as zip_file:
        assert zip_file.namelist() == ["doc-3.xqy"]
        with zip_file.open("doc-3.xqy") as xqy_file:
            assert xqy_file.read() == doc_1_3.content.encode()
    assert doc_1_4.metadata is None
    assert doc_1_4.temporal_collection is None

    doc_2_1 = next((doc for doc in docs if doc.uri == "/root-2/dir/doc-1.xml"), None)
    assert doc_2_1 is not None
    assert type(doc_2_1) is XMLDocument
    assert doc_2_1.doc_type == DocumentType.XML
    _assert_xml_content_with_value(doc_2_1, "value-1")
    assert doc_2_1.metadata is None
    assert doc_2_1.temporal_collection is None

    doc_2_2 = next((doc for doc in docs if doc.uri == "/root-2/dir/doc-2.json"), None)
    assert doc_2_2 is not None
    assert type(doc_2_2) is JSONDocument
    assert doc_2_2.doc_type == DocumentType.JSON
    assert doc_2_2.content == {"root": {"parent": {"child": "value-2"}}}
    assert doc_2_2.metadata is not None
    assert type(doc_2_2.metadata) is Metadata
    assert doc_2_2.metadata.collections() == ["json-doc-2"]
    assert doc_2_2.temporal_collection is None

    doc_2_3 = next((doc for doc in docs if doc.uri == "/root-2/dir/doc-3.xml"), None)
    assert doc_2_3 is not None
    assert type(doc_2_3) is XMLDocument
    assert doc_2_3.doc_type == DocumentType.XML
    _assert_xml_content_with_value(doc_2_3, "value-3")
    assert doc_2_3.metadata is not None
    assert type(doc_2_3.metadata) is Metadata
    assert doc_2_3.metadata.collections() == ["xml-doc-3"]
    assert doc_2_3.temporal_collection is None

    doc_2_4 = next((doc for doc in docs if doc.uri == "/root-2/dir/doc-4.json"), None)
    assert doc_2_4 is not None
    assert type(doc_2_4) is JSONDocument
    assert doc_2_4.doc_type == DocumentType.JSON
    assert doc_2_4.content == {"root": {"parent": {"child": "value-4"}}}
    assert doc_2_4.metadata is not None
    assert type(doc_2_4.metadata) is Metadata
    assert doc_2_4.metadata.collections() == ["json-doc-4"]
    assert doc_2_4.temporal_collection is None

    doc_2_5 = next((doc for doc in docs if doc.uri == "/root-2/dir/doc-5.xml"), None)
    assert doc_2_5 is not None
    assert type(doc_2_5) is XMLDocument
    assert doc_2_5.doc_type == DocumentType.XML
    _assert_xml_content_with_value(doc_2_5, "value-5")
    assert doc_2_5.metadata is not None
    assert type(doc_2_5.metadata) is Metadata
    assert doc_2_5.metadata.collections() == ["xml-doc-5"]
    assert doc_2_5.temporal_collection is None

    doc_2_6 = next((doc for doc in docs if doc.uri == "/root-2/dir/doc-6.json"), None)
    assert doc_2_6 is not None
    assert type(doc_2_6) is JSONDocument
    assert doc_2_6.doc_type == DocumentType.JSON
    assert doc_2_6.content == {"root": {"parent": {"child": "value-6"}}}
    assert doc_2_6.metadata is not None
    assert type(doc_2_6.metadata) is Metadata
    assert doc_2_6.metadata.collections() == ["json-doc-6-json-metadata"]
    assert doc_2_6.temporal_collection is None

    doc_2_7 = next((doc for doc in docs if doc.uri == "/root-2/dir/doc-7.xml"), None)
    assert doc_2_7 is not None
    assert type(doc_2_7) is XMLDocument
    assert doc_2_7.doc_type == DocumentType.XML
    _assert_xml_content_with_value(doc_2_7, "value-7")
    assert doc_2_7.metadata is not None
    assert type(doc_2_7.metadata) is Metadata
    assert doc_2_7.metadata.collections() == ["xml-doc-7-json-metadata"]
    assert doc_2_7.temporal_collection is None


def test_load_document():
    path = f"{TEST_RESOURCES_PATH}/root-1/dir/doc-1.xml"

    doc = DocumentsLoader.load_document(path)
    assert doc is not None
    assert type(doc) is RawDocument
    assert doc.uri is None
    assert doc.doc_type == DocumentType.XML
    assert doc.content == b"<root><parent><child>value-1</child></parent></root>"
    assert doc.metadata is None
    assert doc.temporal_collection is None


def test_load_document_with_uri():
    path = f"{TEST_RESOURCES_PATH}/root-1/dir/doc-1.xml"

    doc = DocumentsLoader.load_document(path, uri="/dir/doc-1.xml")
    assert doc is not None
    assert type(doc) is RawDocument
    assert doc.uri == "/dir/doc-1.xml"
    assert doc.doc_type == DocumentType.XML
    assert doc.content == b"<root><parent><child>value-1</child></parent></root>"
    assert doc.metadata is None
    assert doc.temporal_collection is None


def test_load_document_with_metadata():
    path = f"{TEST_RESOURCES_PATH}/root-2/dir/doc-3.xml"

    doc = DocumentsLoader.load_document(path)
    assert doc is not None
    assert type(doc) is RawDocument
    assert doc.uri is None
    assert doc.doc_type == DocumentType.XML
    assert doc.content == b"<root><parent><child>value-3</child></parent></root>"
    assert doc.metadata == (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">\n'
        b"    <rapi:collections>\n"
        b"        <rapi:collection>xml-doc-3</rapi:collection>\n"
        b"    </rapi:collections>\n"
        b"</rapi:metadata>"
    )
    assert doc.temporal_collection is None


def test_load_document_and_parse():
    path = f"{TEST_RESOURCES_PATH}/root-1/dir/doc-1.xml"

    doc = DocumentsLoader.load_document(path, raw=False)
    assert doc is not None
    assert type(doc) is XMLDocument
    assert doc.uri is None
    assert doc.doc_type == DocumentType.XML
    _assert_xml_content_with_value(doc, "value-1")
    assert doc.metadata is None
    assert doc.temporal_collection is None
    assert doc.content.tag == "root"


def test_load_document_as_documents():
    path = f"{TEST_RESOURCES_PATH}/root-1/dir/doc-1.xml"

    docs = DocumentsLoader.load(path)
    assert type(docs) is GeneratorType

    docs = list(docs)
    assert len(docs) == 1

    doc = docs[0]
    assert doc is not None
    assert type(doc) is RawDocument
    assert doc.uri == "/doc-1.xml"
    assert doc.doc_type == DocumentType.XML
    assert doc.content == b"<root><parent><child>value-1</child></parent></root>"
    assert doc.metadata is None
    assert doc.temporal_collection is None


def test_load_document_as_documents_with_custom_uri_prefix():
    path = f"{TEST_RESOURCES_PATH}/root-1/dir/doc-1.xml"

    docs = DocumentsLoader.load(path, uri_prefix="/custom-root/dir")
    assert type(docs) is GeneratorType

    docs = list(docs)
    assert len(docs) == 1

    doc = docs[0]
    assert doc is not None
    assert type(doc) is RawDocument
    assert doc.uri == "/custom-root/dir/doc-1.xml"
    assert doc.doc_type == DocumentType.XML
    assert doc.content == b"<root><parent><child>value-1</child></parent></root>"
    assert doc.metadata is None
    assert doc.temporal_collection is None


def test_load_document_as_documents_and_parse():
    path = f"{TEST_RESOURCES_PATH}/root-1/dir/doc-1.xml"

    docs = DocumentsLoader.load(path, raw=False)
    assert type(docs) is GeneratorType

    docs = list(docs)
    assert len(docs) == 1

    doc = docs[0]
    assert doc is not None
    assert type(doc) is XMLDocument
    assert doc.uri == "/doc-1.xml"
    assert doc.doc_type == DocumentType.XML
    _assert_xml_content_with_value(doc, "value-1")
    assert doc.metadata is None
    assert doc.temporal_collection is None
    assert doc.content.tag == "root"


def _assert_xml_content_with_value(
    doc: Document,
    value: str,
):
    assert isinstance(doc.content, ElemTree.Element)
    assert doc.content.tag == "root"

    children = list(doc.content)
    assert len(children) == 1
    assert children[0].tag == "parent"

    grandchildren = list(children[0])
    assert len(grandchildren) == 1
    assert grandchildren[0].tag == "child"
    assert grandchildren[0].text == value

    grand_grandchildren = list(grandchildren[0])
    assert len(grand_grandchildren) == 0
