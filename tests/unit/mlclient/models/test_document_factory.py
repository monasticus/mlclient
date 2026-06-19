from xml.etree.ElementTree import Element, ElementTree

import pytest

from mlclient.models import (
    BinaryDocument,
    Document,
    DocumentType,
    JSONDocument,
    Metadata,
    MetadataDocument,
    TextDocument,
    XMLDocument,
)


def test_build_metadata_document_via_metadata_update():
    document = Document.metadata_update("/a.xml", Metadata())

    assert isinstance(document, MetadataDocument)
    assert document.uri == "/a.xml"
    assert document.metadata is not None


def test_create_raises_when_no_content_and_no_doc_type():
    with pytest.raises(TypeError) as err:
        Document.create("/a.xml", metadata=Metadata())

    assert "Document.metadata_update()" in err.value.args[0]


def test_build_document_by_document_type_xml():
    content = Element("root")
    document = Document.create(content=content, doc_type=DocumentType.XML)

    assert isinstance(document, XMLDocument)
    assert isinstance(document.content, ElementTree)
    assert document.content.getroot() is content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_str_document_type_xml():
    content = Element("root")
    document = Document.create(content=content, doc_type="xml")

    assert isinstance(document, XMLDocument)
    assert isinstance(document.content, ElementTree)
    assert document.content.getroot() is content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_content_type_xml():
    content = Element("root")
    document = Document.create(content=content)

    assert isinstance(document, XMLDocument)
    assert isinstance(document.content, ElementTree)
    assert document.content.getroot() is content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_document_type_json():
    content = {"root": "data"}
    document = Document.create(content=content, doc_type=DocumentType.JSON)

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_str_document_type_json():
    content = {"root": "data"}
    document = Document.create(content=content, doc_type="json")

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_content_type_json():
    content = {"root": "data"}
    document = Document.create(content=content)

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = Document.create(content=content, doc_type=DocumentType.TEXT)

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_str_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = Document.create(content=content, doc_type="text")

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_content_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = Document.create(content=content)

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_document_type_binary():
    content = b'{"root": "data"}'
    document = Document.create(content=content, doc_type=DocumentType.BINARY)

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_by_str_document_type_binary():
    content = b'{"root": "data"}'
    document = Document.create(content=content, doc_type="binary")

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_by_content_type_binary():
    content = b'{"root": "data"}'
    document = Document.create(content=content)

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_unsupported_content_type():
    with pytest.raises(NotImplementedError) as err:
        Document.create(content=1)

    expected_msg = (
        "Unsupported document type! Document types are: XML, JSON, TEXT, BINARY!"
    )
    assert err.value.args[0] == expected_msg


def test_build_document_by_uri_xml():
    document = Document.create("/doc.xml", "<root/>")

    assert isinstance(document, XMLDocument)
    assert document.doc_type == DocumentType.XML


def test_build_document_by_uri_json():
    document = Document.create("/doc.json", '{"key": "val"}')

    assert isinstance(document, JSONDocument)
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_uri_text():
    document = Document.create("/doc.xqy", "xquery version '1.0-ml';")

    assert isinstance(document, TextDocument)
    assert document.doc_type == DocumentType.TEXT


def test_build_document_str_no_uri_falls_back_to_text():
    document = Document.create(content="<root/>")

    assert isinstance(document, TextDocument)
    assert document.doc_type == DocumentType.TEXT


def test_build_document_bytes_no_uri_falls_back_to_binary():
    document = Document.create(content=b"<root/>")

    assert isinstance(document, BinaryDocument)
    assert document.doc_type == DocumentType.BINARY


# --- URI-inference with bytes ---


def test_build_document_by_uri_xml_bytes():
    document = Document.create("/doc.xml", b"<root/>")

    assert isinstance(document, XMLDocument)
    assert document.doc_type == DocumentType.XML


def test_build_document_by_uri_json_bytes():
    document = Document.create("/doc.json", b'{"key": "val"}')

    assert isinstance(document, JSONDocument)
    assert document.doc_type == DocumentType.JSON


# --- Typed factory methods ---


def test_typed_factory_xml():
    doc = Document.xml("/x.xml", "<root/>")
    assert isinstance(doc, XMLDocument)
    assert doc.doc_type == DocumentType.XML


def test_typed_factory_xml_from_element():
    element = Element("root")
    doc = Document.xml("/x.xml", element)
    assert isinstance(doc, XMLDocument)
    assert doc.content.getroot() is element


def test_typed_factory_json_from_dict():
    doc = Document.json("/x.json", {"k": "v"})
    assert isinstance(doc, JSONDocument)
    assert doc.content == {"k": "v"}


def test_typed_factory_json_from_str():
    doc = Document.json("/x.json", '{"k": "v"}')
    assert isinstance(doc, JSONDocument)
    assert doc.content == {"k": "v"}


def test_typed_factory_text():
    doc = Document.text("/x.txt", "hello")
    assert isinstance(doc, TextDocument)
    assert doc.content == "hello"


def test_typed_factory_binary():
    doc = Document.binary("/x.bin", b"\x00\x01")
    assert isinstance(doc, BinaryDocument)
    assert doc.content == b"\x00\x01"


# --- metadata_update() edge cases ---


def test_metadata_update_blank_uri_raises():
    with pytest.raises(TypeError) as err:
        Document.metadata_update("", Metadata())
    assert "uri is required" in err.value.args[0]


def test_metadata_update_whitespace_uri_raises():
    with pytest.raises(TypeError) as err:
        Document.metadata_update("   ", Metadata())
    assert "uri is required" in err.value.args[0]


def test_metadata_update_none_metadata_raises():
    with pytest.raises(TypeError) as err:
        Document.metadata_update("/x.xml", None)
    assert "metadata is required" in err.value.args[0]


def test_metadata_update_empty_metadata_allowed():
    doc = Document.metadata_update("/x.xml", Metadata())
    assert isinstance(doc, MetadataDocument)


def test_metadata_update_raw_bytes_metadata():
    doc = Document.metadata_update("/x.xml", b'{"collections": ["c1"]}')
    assert isinstance(doc, MetadataDocument)
    assert isinstance(doc.metadata, Metadata)
    assert doc.metadata.collections() == ["c1"]


def test_metadata_update_raw_str_metadata():
    doc = Document.metadata_update("/x.xml", '{"collections": ["c1"]}')
    assert isinstance(doc, MetadataDocument)
    assert isinstance(doc.metadata, Metadata)
    assert doc.metadata.collections() == ["c1"]
