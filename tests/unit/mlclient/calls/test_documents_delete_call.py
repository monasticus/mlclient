import pytest

from mlclient import exceptions
from mlclient.calls import DocumentsDeleteCall


@pytest.fixture()
def default_documents_get_call():
    """Returns an DocumentsDeleteCall instance"""
    return DocumentsDeleteCall(uri="/a.xml")


def test_validation_category_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsDeleteCall(uri="/a.xml", category="X")

    expected_msg = (
        "The supported categories are: "
        "content, metadata, metadata-values, collections, "
        "permissions, properties, quality"
    )
    assert err.value.args[0] == expected_msg


def test_validation_multiple_categories_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsDeleteCall(uri="/a.xml", category=["collections", "X"])

    expected_msg = (
        "The supported categories are: "
        "content, metadata, metadata-values, collections, "
        "permissions, properties, quality"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint(default_documents_get_call):
    assert default_documents_get_call.endpoint == "/v1/documents"


def test_method(default_documents_get_call):
    assert default_documents_get_call.method == "DELETE"


def test_parameters_single_uri():
    assert DocumentsDeleteCall(uri="/a.xml").params == {
        "uri": "/a.xml",
    }


def test_parameters_multiple_uris():
    assert DocumentsDeleteCall(uri=["/a.xml", "/b.xml"]).params == {
        "uri": ["/a.xml", "/b.xml"],
    }


def test_parameters_single_category():
    assert DocumentsDeleteCall(
        uri="/a.xml",
        category="collections",
    ).params == {
        "uri": "/a.xml",
        "category": "collections",
    }


def test_parameters_multiple_categories():
    assert DocumentsDeleteCall(
        uri="/a.xml",
        category=["collections", "permissions"],
    ).params == {
        "uri": "/a.xml",
        "category": ["collections", "permissions"],
    }


def test_headers(default_documents_get_call):
    assert default_documents_get_call.headers == {}


def test_body(default_documents_get_call):
    assert default_documents_get_call.body is None


def test_fully_parametrized_call_for_single_uri():
    call = DocumentsDeleteCall(
        uri="/a.xml",
        database="Documents",
        category="content",
        txid="transaction",
        temporal_collection="Entity-collection",
        system_time="2023-09-09T01:01:01.000Z",
        wipe_temporal=True,
    )
    assert call.method == "DELETE"
    assert call.headers == {}
    assert call.params == {
        "uri": "/a.xml",
        "database": "Documents",
        "category": "content",
        "txid": "transaction",
        "temporal-collection": "Entity-collection",
        "system-time": "2023-09-09T01:01:01.000Z",
        "result": "wipe",
    }
    assert call.body is None


def test_fully_parametrized_call_for_multiple_uris():
    call = DocumentsDeleteCall(
        uri=["/a.xml", "/b.xml"],
        database="Documents",
        category="content",
        txid="transaction",
        temporal_collection="Entity-collection",
        system_time="2023-09-09T01:01:01.000Z",
        wipe_temporal=True,
    )
    assert call.method == "DELETE"
    assert call.headers == {}
    assert call.params == {
        "uri": ["/a.xml", "/b.xml"],
        "database": "Documents",
        "category": "content",
        "txid": "transaction",
        "temporal-collection": "Entity-collection",
        "system-time": "2023-09-09T01:01:01.000Z",
        "result": "wipe",
    }
    assert call.body is None
