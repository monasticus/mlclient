from mlclient.model import Document, StringDocument


def test_is_document_subclass():
    assert issubclass(StringDocument, Document)


def test_content():
    document = StringDocument('{"root": "data"}')
    assert document.content == '{"root": "data"}'
