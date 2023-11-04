from mlclient.model import Document, DocumentType, TextDocument


def test_is_document_subclass():
    assert issubclass(TextDocument, Document)


def test_content():
    document = TextDocument('xquery version "1.0-ml";\nfn:current-dateTime()')
    assert document.content == 'xquery version "1.0-ml";\nfn:current-dateTime()'


def test_doc_type():
    assert TextDocument("").doc_type == DocumentType.TEXT
