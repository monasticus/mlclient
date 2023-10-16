from xml.etree.ElementTree import Element

from mlclient.model import DocumentType, DocumentFactory


def test_build_document_by_document_type_xml():
    content = Element("root")
    document = DocumentFactory.build_document(content, DocumentType.XML)

    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_str_document_type_xml():
    content = Element("root")
    document = DocumentFactory.build_document(content, "xml")

    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_document_by_document_type_json():
    content = {"root": "data"}
    document = DocumentFactory.build_document(content, DocumentType.JSON)

    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_str_document_type_json():
    content = {"root": "data"}
    document = DocumentFactory.build_document(content, "json")

    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_document_by_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = DocumentFactory.build_document(content, DocumentType.TEXT)

    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_str_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = DocumentFactory.build_document(content, "text")

    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_build_document_by_document_type_binary():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_document(content, DocumentType.BINARY)

    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_document_by_str_document_type_binary():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_document(content, "binary")

    assert document.content == content
    assert document.doc_type == DocumentType.BINARY


def test_build_raw_document_bytes_with_document_type():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_raw_document(content, DocumentType.JSON)

    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_raw_document_bytes_with_str_document_type():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_raw_document(content, "json")

    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_build_raw_document_str_with_document_type():
    content = "<root></root>"
    document = DocumentFactory.build_raw_document(content, DocumentType.XML)

    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_build_raw_document_str_with_str_document_type():
    content = "<root></root>"
    document = DocumentFactory.build_raw_document(content, "xml")

    assert document.content == content
    assert document.doc_type == DocumentType.XML

