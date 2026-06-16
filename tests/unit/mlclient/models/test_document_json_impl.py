import pytest

from mlclient.models import Document, DocumentType, JSONDocument


def test_is_document_subclass():
    assert issubclass(JSONDocument, Document)


def test_none_content_raises():
    with pytest.raises(TypeError, match="JSONDocument requires content"):
        JSONDocument(None)


def test_content_from_dict():
    document = JSONDocument({"root": "data"})
    assert document.content == {"root": "data"}


def test_content_from_str_lazy_parse():
    json_str = '{"root": "data"}'

    document = JSONDocument(json_str)
    parsed = document.content
    assert parsed == {"root": "data"}
    assert document.content is parsed  # cached


def test_content_from_bytes_lazy_parse():
    json_bytes = b'{"root": "data"}'

    document = JSONDocument(json_bytes)
    parsed = document.content
    assert parsed == {"root": "data"}
    assert document.content is parsed  # cached


def test_content_bytes_from_dict():
    document = JSONDocument({"root": "data"})
    assert document.content_bytes == b'{"root": "data"}'


def test_content_bytes_from_str_no_parse():
    invalid_json = "this is not json"

    document = JSONDocument(invalid_json)
    assert document.content_bytes == invalid_json.encode("utf-8")


def test_content_bytes_from_bytes_zero_copy():
    json_bytes = b"this is not json"

    document = JSONDocument(json_bytes)
    assert document.content_bytes is json_bytes


def test_content_string_from_dict():
    document = JSONDocument({"root": "data"})
    assert document.content_string == '{"root": "data"}'


def test_content_string_from_str_zero_copy():
    invalid_json = "this is not json"

    document = JSONDocument(invalid_json)
    assert document.content_string is invalid_json


def test_content_string_from_bytes_no_parse():
    invalid_json = b"this is not json"

    document = JSONDocument(invalid_json)
    assert document.content_string == "this is not json"


def test_invalidate_after_dict_mutation_reserializes():
    document = JSONDocument({"root": "data"})
    initial = document.content_bytes
    assert initial == b'{"root": "data"}'

    document.content["root"] = "updated"
    chained = document.invalidate()
    assert chained is document
    assert document.content_bytes == b'{"root": "updated"}'


def test_invalidate_without_parsed_keeps_raw():
    document = JSONDocument(b'{"root": "data"}')
    assert document.invalidate() is document
    assert document.content_bytes == b'{"root": "data"}'


def test_doc_type():
    assert JSONDocument({"root": "data"}).doc_type == DocumentType.JSON
