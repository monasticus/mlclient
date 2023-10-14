from mlclient.model import Document, DocumentType, RawDocument


def test_is_document_subclass():
    assert issubclass(RawDocument, Document)


def test_content():
    document = RawDocument(b'{"root": "data"}', doc_type=DocumentType.JSON)
    assert document.content == b'{"root": "data"}'
    assert document.doc_type == DocumentType.JSON


def test_doc_type_when_none():
    assert RawDocument(b"").doc_type == DocumentType.XML
