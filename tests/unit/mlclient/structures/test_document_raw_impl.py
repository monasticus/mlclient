from mlclient.structures import Document, DocumentType, RawDocument


def test_is_document_subclass():
    assert issubclass(RawDocument, Document)


def test_content():
    document = RawDocument(b'{"root": "data"}', doc_type=DocumentType.JSON)
    assert document.content == b'{"root": "data"}'
    assert document.doc_type == DocumentType.JSON


def test_content_bytes():
    document = RawDocument(b'{"root": "data"}', doc_type=DocumentType.JSON)
    assert document.content_bytes == b'{"root": "data"}'
    assert document.doc_type == DocumentType.JSON


def test_content_string():
    document = RawDocument(b'{"root": "data"}', doc_type=DocumentType.JSON)
    assert document.content_string == '{"root": "data"}'
    assert document.doc_type == DocumentType.JSON


def test_doc_type_when_none():
    assert RawDocument(b"").doc_type == DocumentType.XML
