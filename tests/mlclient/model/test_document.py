from mlclient.model import Document, DocumentType, Metadata, Permission


class DocumentTestImpl(Document):

    @property
    def content(self):
        return ""


class DocumentTestInvalidImpl(Document):
    """A Document invalid implementation for testing purposes"""


def test_issubclass_true():
    assert issubclass(DocumentTestImpl, Document)


def test_issubclass_false():
    assert not issubclass(DocumentTestInvalidImpl, Document)


def test_document_uri():
    uri = "/some/path/to/document.xml"
    document = DocumentTestImpl(uri=uri)
    assert document.uri == uri


def test_document_uri_when_none():
    assert DocumentTestImpl().uri is None


def test_document_uri_when_blank():
    document = DocumentTestImpl(uri=" \n")
    assert document.uri is None


def test_doc_type():
    doc_type = DocumentType.JSON
    document = DocumentTestImpl(doc_type=doc_type)
    assert document.doc_type == doc_type


def test_doc_type_when_none():
    assert DocumentTestImpl().doc_type == DocumentType.XML


def test_metadata():
    metadata = Metadata(collections=["custom-collection"],
                        permissions=[Permission("custom-role", {Permission.READ})])
    document = DocumentTestImpl(metadata=metadata)
    assert document.metadata == metadata
    assert document.metadata is not metadata


def test_metadata_when_none():
    assert DocumentTestImpl().metadata is None


def test_is_temporal():
    document = DocumentTestImpl(is_temporal=True)
    assert document.is_temporal is True


def test_is_temporal_when_none():
    assert DocumentTestImpl().is_temporal is False


def test_content():
    document = DocumentTestImpl()
    assert document.content == ""
