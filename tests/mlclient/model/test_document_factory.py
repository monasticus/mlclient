from xml.etree.ElementTree import Element

from mlclient.model import DocumentType, DocumentFactory


def test_get_by_document_type_xml():
    content = Element("root")
    document = DocumentFactory.build_document(content, DocumentType.XML)

    assert document.content == content
    assert document.doc_type == DocumentType.XML


def test_get_by_document_type_json():
    content = {"root": "data"}
    document = DocumentFactory.build_document(content, DocumentType.JSON)

    assert document.content == content
    assert document.doc_type == DocumentType.JSON


def test_get_by_document_type_text():
    content = 'xquery version "1.0-ml";\nfn:current-dateTime()'
    document = DocumentFactory.build_document(content, DocumentType.TEXT)

    assert document.content == content
    assert document.doc_type == DocumentType.TEXT


def test_get_by_document_type_binary():
    content = b'{"root": "data"}'
    document = DocumentFactory.build_document(content, DocumentType.BINARY)

    assert document.content == content
    assert document.doc_type == DocumentType.BINARY
