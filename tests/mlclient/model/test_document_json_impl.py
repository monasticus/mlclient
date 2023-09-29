from mlclient.model import Document, DocumentType, JSONDocument


def test_is_document_subclass():
    assert issubclass(JSONDocument, Document)


def test_content():
    document = JSONDocument({"root": "data"})
    assert document.content == {"root": "data"}


def test_doc_type_when_none():
    assert JSONDocument({"root": "data"}).doc_type == DocumentType.JSON
