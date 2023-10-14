from mlclient.model import Document, DocumentType, RawStringDocument


def test_is_document_subclass():
    assert issubclass(RawStringDocument, Document)


def test_content():
    document = RawStringDocument('{"root": "data"}', doc_type=DocumentType.JSON)
    assert document.content == '{"root": "data"}'
    assert document.doc_type == DocumentType.JSON


def test_doc_type_when_none():
    assert RawStringDocument("").doc_type == DocumentType.XML
