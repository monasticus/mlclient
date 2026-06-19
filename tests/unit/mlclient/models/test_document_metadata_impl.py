from mlclient.models import Document, Metadata, MetadataDocument


def test_is_document_subclass():
    assert issubclass(MetadataDocument, Document)


def test_content():
    document = MetadataDocument(uri="/a.xml", metadata=Metadata())
    assert document.uri == "/a.xml"
    assert document.content is None
    assert document.content_bytes is None
    assert document.content_string is None
    assert document.doc_type is None
    assert document.metadata is not None
    assert document.temporal_collection is None


def test_temporal_collection():
    document = MetadataDocument(
        uri="/a.xml",
        metadata=Metadata(),
        temporal_collection="my-temporal",
    )
    assert document.temporal_collection == "my-temporal"


def test_metadata_as_bytes():
    document = MetadataDocument(uri="/a.xml", metadata=b'{"collections": ["c1"]}')
    assert isinstance(document.metadata, Metadata)
    assert document.metadata.collections() == ["c1"]


def test_metadata_as_str():
    document = MetadataDocument(uri="/a.xml", metadata='{"collections": ["c1"]}')
    assert isinstance(document.metadata, Metadata)
    assert document.metadata.collections() == ["c1"]
