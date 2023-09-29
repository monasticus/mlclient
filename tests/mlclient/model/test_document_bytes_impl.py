from mlclient.model import BytesDocument, Document, DocumentType


def test_is_document_subclass():
    assert issubclass(BytesDocument, Document)


def test_content():
    document = BytesDocument(b'{"root": "data"}')
    assert document.content == b'{"root": "data"}'


def test_doc_type_when_none():
    assert BytesDocument(b'{"root": "data"}').doc_type == DocumentType.XML
