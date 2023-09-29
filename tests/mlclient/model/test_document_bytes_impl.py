from mlclient.model import BytesDocument, Document


def test_is_document_subclass():
    assert issubclass(BytesDocument, Document)


def test_content():
    document = BytesDocument(b'{"root": "data"}')
    assert document.content == b'{"root": "data"}'
