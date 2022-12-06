from mlclient.model import Document, DocumentType, Metadata, Permission


def test_document_uri():
    uri = "/some/path/to/document.xml"
    document = Document(uri=uri)
    assert document.uri() == uri


def test_document_uri_when_none():
    assert Document().uri() is None


def test_document_uri_when_blank():
    document = Document(uri=" \n")
    assert document.uri() is None


def test_doc_type():
    doc_type = DocumentType.JSON
    document = Document(doc_type=doc_type)
    assert document.doc_type() == doc_type


def test_doc_type_when_none():
    assert Document().doc_type() == DocumentType.XML


def test_metadata():
    metadata = Metadata(collections=["custom-collection"],
                        permissions=[Permission("custom-role", {Permission.READ})])
    document = Document(metadata=metadata)
    assert document.metadata() == metadata
    assert document.metadata() is not metadata


def test_metadata_when_none():
    assert Document().metadata() is None


def test_is_temporal():
    document = Document(is_temporal=True)
    assert document.is_temporal() is True


def test_is_temporal_when_none():
    assert Document().is_temporal() is False
