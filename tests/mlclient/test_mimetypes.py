from mlclient.mimetypes import Mimetypes
from mlclient.model import DocumentType


def test_xml_mimetypes():
    mimetypes = Mimetypes.get_mimetypes(DocumentType.XML)
    assert len(mimetypes) > 0
    assert "application/xml" in mimetypes


def test_json_mimetypes():
    mimetypes = Mimetypes.get_mimetypes(DocumentType.JSON)
    assert len(mimetypes) > 0
    assert "application/json" in mimetypes


def test_text_mimetypes():
    mimetypes = Mimetypes.get_mimetypes(DocumentType.TEXT)
    assert len(mimetypes) > 0
    assert "text/html" in mimetypes


def test_bin_mimetypes():
    mimetypes = Mimetypes.get_mimetypes(DocumentType.BINARY)
    assert len(mimetypes) > 0
    assert "image/png" in mimetypes


def test_doc_type_for_uri_xml():
    doc_type = Mimetypes.get_doc_type("/some/dir/doc1.xml")
    assert doc_type == DocumentType.XML


def test_doc_type_for_uri_json():
    doc_type = Mimetypes.get_doc_type("/some/dir/doc2.json")
    assert doc_type == DocumentType.JSON


def test_doc_type_for_uri_text():
    doc_type = Mimetypes.get_doc_type("/some/dir/doc3.xqy")
    assert doc_type == DocumentType.TEXT


def test_doc_type_for_uri_bin():
    doc_type = Mimetypes.get_doc_type("/some/dir/doc4.zip")
    assert doc_type == DocumentType.BINARY


def test_doc_type_for_uri_bin_unknown_ext():
    doc_type = Mimetypes.get_doc_type("/some/dir/doc5")
    assert doc_type == DocumentType.BINARY
