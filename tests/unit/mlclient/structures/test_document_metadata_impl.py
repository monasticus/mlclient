from mlclient.structures import Document, Metadata, MetadataDocument


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
