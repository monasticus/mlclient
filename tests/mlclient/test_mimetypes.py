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


def test_binary_mimetypes():
    mimetypes = Mimetypes.get_mimetypes(DocumentType.BINARY)
    assert len(mimetypes) > 0
    assert "image/png" in mimetypes
