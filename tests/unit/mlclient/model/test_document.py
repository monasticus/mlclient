from mlclient.model import Document, DocumentType, Metadata, Permission


class DocumentTestImpl(Document):
    @property
    def content(self):
        return ""

    @property
    def content_bytes(self):
        return b""

    @property
    def content_string(self):
        return self.content


class DocumentTestInvalidImpl1(Document):
    """A Document invalid implementation for testing purposes"""


class DocumentTestInvalidImpl2(Document):
    """A Document invalid implementation for testing purposes"""

    @property
    def content(self):
        return ""


class DocumentTestInvalidImpl3(Document):
    """A Document invalid implementation for testing purposes"""

    @property
    def content_bytes(self):
        return b""


class DocumentTestInvalidImpl4(Document):
    """A Document invalid implementation for testing purposes"""

    @property
    def content_string(self):
        return ""


class DocumentTestInvalidImpl5(Document):
    """A Document invalid implementation for testing purposes"""

    @property
    def content(self):
        return ""

    @property
    def content_bytes(self):
        return b""


class DocumentTestInvalidImpl6(Document):
    """A Document invalid implementation for testing purposes"""

    @property
    def content(self):
        return ""

    @property
    def content_string(self):
        return ""


class DocumentTestInvalidImpl7(Document):
    """A Document invalid implementation for testing purposes"""

    @property
    def content_bytes(self):
        return b""

    @property
    def content_string(self):
        return ""


def test_issubclass_true():
    assert issubclass(DocumentTestImpl, Document)


def test_issubclass_false():
    assert not issubclass(DocumentTestInvalidImpl1, Document)
    assert not issubclass(DocumentTestInvalidImpl2, Document)
    assert not issubclass(DocumentTestInvalidImpl3, Document)
    assert not issubclass(DocumentTestInvalidImpl4, Document)
    assert not issubclass(DocumentTestInvalidImpl5, Document)
    assert not issubclass(DocumentTestInvalidImpl6, Document)
    assert not issubclass(DocumentTestInvalidImpl7, Document)


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
    metadata = Metadata(
        collections=["custom-collection"],
        permissions=[Permission("custom-role", {Permission.READ})],
    )
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


def test_content_bytes():
    document = DocumentTestImpl()
    assert document.content_bytes == b""


def test_content_string():
    document = DocumentTestImpl()
    assert document.content_string == ""
