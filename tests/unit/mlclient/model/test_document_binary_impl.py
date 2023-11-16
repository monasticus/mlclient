from mlclient.model import BinaryDocument, Document, DocumentType


def test_is_document_subclass():
    assert issubclass(BinaryDocument, Document)


def test_content():
    document = BinaryDocument(b'{"root": "data"}')
    assert document.content == b'{"root": "data"}'


def test_doc_type():
    assert BinaryDocument(b'{"root": "data"}').doc_type == DocumentType.BINARY
