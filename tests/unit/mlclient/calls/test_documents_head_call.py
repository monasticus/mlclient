import pytest

from mlclient import exceptions
from mlclient.calls import ApiCall, DocumentsHeadCall


def test_is_api_call():
    assert issubclass(DocumentsHeadCall, ApiCall)


def test_validation_category_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsHeadCall(uri="/a.json", category="X")

    assert str(err.value) == (
        "The supported categories are: "
        "content, metadata, metadata-values, collections, "
        "permissions, properties, quality"
    )


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsHeadCall(uri="/a.json", category="metadata", data_format="text")

    assert str(err.value) == (
        "The format applies to metadata only; supported formats are: json, xml"
    )


def test_endpoint():
    assert DocumentsHeadCall(uri="/a.json").endpoint == "/v1/documents"


def test_method():
    assert DocumentsHeadCall(uri="/a.json").method == "HEAD"


def test_parameters():
    assert DocumentsHeadCall(uri="/a.json").params == {"uri": "/a.json"}


def test_parameters_multiple_categories():
    assert DocumentsHeadCall(
        uri="/a.json",
        category=["content", "metadata"],
    ).params == {
        "uri": "/a.json",
        "category": ["content", "metadata"],
    }


def test_headers():
    assert DocumentsHeadCall(uri="/a.json").headers == {}


def test_headers_for_metadata_category_and_json_format():
    assert DocumentsHeadCall(
        uri="/a.json",
        category="metadata",
        data_format="json",
    ).headers == {
        "Accept": "application/json",
    }


def test_headers_for_multiple_categories():
    assert DocumentsHeadCall(
        uri="/a.json",
        category=["content", "metadata"],
    ).headers == {
        "Accept": "multipart/mixed",
    }


def test_body():
    assert DocumentsHeadCall(uri="/a.json").body is None


def test_fully_parametrized_call():
    call = DocumentsHeadCall(
        uri="/a.json",
        database="Documents",
        category="collections",
        data_format="xml",
        txid="12345",
    )

    assert call.method == "HEAD"
    assert call.endpoint == "/v1/documents"
    assert call.headers == {
        "Accept": "application/xml",
    }
    assert call.params == {
        "uri": "/a.json",
        "database": "Documents",
        "category": "collections",
        "format": "xml",
        "txid": "12345",
    }
    assert call.body is None
