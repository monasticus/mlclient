from xml.etree.ElementTree import Element

import pytest

from mlclient.structures import (
    BinaryDocument,
    Document,
    DocumentType,
    JSONDocument,
    Metadata,
    MetadataDocument,
    RawDocument,
    RawStringDocument,
    TextDocument,
    XMLDocument,
)


def test_build_metadata_document():
    document = Document.create(uri="/a.xml", metadata=Metadata())

    assert isinstance(document, MetadataDocument)
    assert document.uri == "/a.xml"
    assert document.metadata is not None


def test_build_document_by_document_type_xml():
    content = Element("root")
    document = Document.create(content, DocumentType.XML)

    assert isinstance(document, XMLDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_str_document_type_xml():
    content = Element("root")
    document = Document.create(content, "xml")

    assert isinstance(document, XMLDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_content_type_xml():
    content = Element("root")
    document = Document.create(content)

    assert isinstance(document, XMLDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_document_type_json():
    content = {"root": "data"}
    document = Document.create(content, DocumentType.JSON)

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_str_document_type_json():
    content = {"root": "data"}
    document = Document.create(content, "json")

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_content_type_json():
    content = {"root": "data"}
    document = Document.create(content)

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = Document.create(content, DocumentType.TEXT)

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_str_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = Document.create(content, "text")

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_content_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = Document.create(content)

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_document_type_binary():
    content = b'{"root": "data"}'
    document = Document.create(content, DocumentType.BINARY)

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_by_str_document_type_binary():
    content = b'{"root": "data"}'
    document = Document.create(content, "binary")

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_by_content_type_binary():
    content = b'{"root": "data"}'
    document = Document.create(content)

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_unsupported_content_type():
    with pytest.raises(NotImplementedError) as err:
        Document.create(1)

    expected_msg = (
        "Unsupported document type! Document types are: XML, JSON, TEXT, BINARY!"
    )
    assert err.value.args[0] == expected_msg


def test_build_raw_document_bytes_with_document_type():
    content = b'{"root": "data"}'
    document = Document.create_raw(content, DocumentType.JSON)

    assert isinstance(document, RawDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_raw_document_bytes_with_str_document_type():
    content = b'{"root": "data"}'
    document = Document.create_raw(content, "json")

    assert isinstance(document, RawDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_raw_document_str_with_document_type():
    content = "<root></root>"
    document = Document.create_raw(content, DocumentType.XML)

    assert isinstance(document, RawStringDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_raw_document_str_with_str_document_type():
    content = "<root></root>"
    document = Document.create_raw(content, "xml")

    assert isinstance(document, RawStringDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_raw_document_unsupported_content_type():
    with pytest.raises(NotImplementedError) as err:
        Document.create_raw({}, DocumentType.JSON)

    expected_msg = "Raw document can store content only in [bytes] or [str] format!"
    assert err.value.args[0] == expected_msg
