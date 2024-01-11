from types import GeneratorType

from mlclient.jobs import DocumentsLoader
from mlclient.model import DocumentType, RawDocument
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

    doc_3 = next((doc for doc in docs if doc.uri == "/dir/doc-3.xml"), None)
    assert doc_3 is not None
    assert type(doc_3) is RawDocument
    assert doc_3.doc_type == DocumentType.XML
    assert doc_3.content == b"<root><parent><child>value-3</child></parent></root>"
    assert doc_3.metadata is None
    assert doc_3.temporal_collection is None

    doc_4 = next((doc for doc in docs if doc.uri == "/dir/doc-4.json"), None)
    assert doc_4 is not None
    assert type(doc_4) is RawDocument
    assert doc_4.doc_type == DocumentType.JSON
    assert doc_4.content == b'{"root": {"parent": {"child": "value-4"}}}'
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
    doc_2 = next((doc for doc in docs if doc.uri == "/custom-root/dir/doc-2.json"), None)
    assert doc_2 is not None

    doc_3 = next((doc for doc in docs if doc.uri == "/dir/doc-3.xml"), None)
    assert doc_3 is None
    doc_3 = next((doc for doc in docs if doc.uri == "/custom-root/dir/doc-3.xml"), None)
    assert doc_3 is not None

    doc_4 = next((doc for doc in docs if doc.uri == "/dir/doc-4.json"), None)
    assert doc_4 is None
    doc_4 = next((doc for doc in docs if doc.uri == "/custom-root/dir/doc-4.json"), None)
    assert doc_4 is not None
