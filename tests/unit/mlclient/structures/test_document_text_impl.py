from mlclient.structures import Document, DocumentType, TextDocument


def test_is_document_subclass():
    assert issubclass(TextDocument, Document)


def test_content():
    document = TextDocument('xquery version "1.0-ml";\nfn:current-dateTime()')
    assert document.content == 'xquery version "1.0-ml";\nfn:current-dateTime()'


def test_content_bytes():
    document = TextDocument('xquery version "1.0-ml";\nfn:current-dateTime()')
    assert document.content_bytes == b'xquery version "1.0-ml";\nfn:current-dateTime()'


def test_content_string():
    document = TextDocument('xquery version "1.0-ml";\nfn:current-dateTime()')
    assert document.content_string == 'xquery version "1.0-ml";\nfn:current-dateTime()'


def test_doc_type():
    assert TextDocument("").doc_type == DocumentType.TEXT
