from mlclient.structures import Document, DocumentType, JSONDocument


def test_is_document_subclass():
    assert issubclass(JSONDocument, Document)


def test_content():
    document = JSONDocument({"root": "data"})
    assert document.content == {"root": "data"}


def test_content_bytes():
    document = JSONDocument({"root": "data"})
    assert document.content_bytes == b'{"root": "data"}'


def test_content_string():
    document = JSONDocument({"root": "data"})
    assert document.content_string == '{"root": "data"}'


def test_doc_type():
    assert JSONDocument({"root": "data"}).doc_type == DocumentType.JSON
