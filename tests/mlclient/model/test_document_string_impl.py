from mlclient.model import Document, DocumentType, StringDocument


def test_is_document_subclass():
    assert issubclass(StringDocument, Document)


def test_content():
    document = StringDocument('{"root": "data"}')
    assert document.content == '{"root": "data"}'


def test_doc_type_when_none():
    assert StringDocument('{"root": "data"}').doc_type == DocumentType.XML
