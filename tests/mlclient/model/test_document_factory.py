from xml.etree.ElementTree import Element

import pytest

from mlclient.model import (
    BinaryDocument,
    DocumentFactory,
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
    document = DocumentFactory.build_document(uri="/a.xml", metadata=Metadata())

    assert isinstance(document, MetadataDocument)
    assert document.uri == "/a.xml"
    assert document.metadata is not None


def test_build_document_by_document_type_xml():
    content = Element("root")
    document = DocumentFactory.build_document(content, DocumentType.XML)

    assert isinstance(document, XMLDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_str_document_type_xml():
    content = Element("root")
    document = DocumentFactory.build_document(content, "xml")

    assert isinstance(document, XMLDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_content_type_xml():
    content = Element("root")
    document = DocumentFactory.build_document(content)

    assert isinstance(document, XMLDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_document_type_json():
    content = {"root": "data"}
    document = DocumentFactory.build_document(content, DocumentType.JSON)

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_str_document_type_json():
    content = {"root": "data"}
    document = DocumentFactory.build_document(content, "json")

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_content_type_json():
    content = {"root": "data"}
    document = DocumentFactory.build_document(content)

    assert isinstance(document, JSONDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = DocumentFactory.build_document(content, DocumentType.TEXT)

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_str_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = DocumentFactory.build_document(content, "text")

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_content_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = DocumentFactory.build_document(content)

    assert isinstance(document, TextDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_document_type_binary():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_document(content, DocumentType.BINARY)

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_by_str_document_type_binary():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_document(content, "binary")

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_by_content_type_binary():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_document(content)

    assert isinstance(document, BinaryDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_unsupported_content_type():
    with pytest.raises(NotImplementedError) as err:
        DocumentFactory.build_document(1)

    expected_msg = (
        "Unsupported document type! Document types are: XML, JSON, TEXT, BINARY!"
    )
    assert err.value.args[0] == expected_msg


def test_build_raw_document_bytes_with_document_type():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_raw_document(content, DocumentType.JSON)

    assert isinstance(document, RawDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_raw_document_bytes_with_str_document_type():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_raw_document(content, "json")

    assert isinstance(document, RawDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_raw_document_str_with_document_type():
    content = "<root></root>"
    document = DocumentFactory.build_raw_document(content, DocumentType.XML)

    assert isinstance(document, RawStringDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_raw_document_str_with_str_document_type():
    content = "<root></root>"
    document = DocumentFactory.build_raw_document(content, "xml")

    assert isinstance(document, RawStringDocument)
    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_raw_document_unsupported_content_type():
    with pytest.raises(NotImplementedError) as err:
        DocumentFactory.build_raw_document({}, DocumentType.JSON)

    expected_msg = "Raw document can store content only in [bytes] or [str] format!"
    assert err.value.args[0] == expected_msg
