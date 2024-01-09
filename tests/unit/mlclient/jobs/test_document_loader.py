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
