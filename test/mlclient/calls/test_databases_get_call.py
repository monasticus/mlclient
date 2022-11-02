import pytest

from mlclient import exceptions
from mlclient.calls import DatabasesGetCall


@pytest.fixture
def default_databases_get_call():
    """Returns an DatabasesGetCall instance"""
    return DatabasesGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasesGetCall(data_format="text")

    assert err.value.args[0] == "The supported formats are: xml, json, html"


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasesGetCall(view="X")

    assert err.value.args[0] == "The supported views are: " \
                                "describe, default, metrics, package, schema, properties-schema"


def test_endpoint(default_databases_get_call):
    assert default_databases_get_call.endpoint() == "/manage/v2/databases"
    assert default_databases_get_call.ENDPOINT == "/manage/v2/databases"
    assert DatabasesGetCall.ENDPOINT == "/manage/v2/databases"


def test_method(default_databases_get_call):
    assert default_databases_get_call.method() == "GET"


def test_headers_for_default_format():
    call = DatabasesGetCall()
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_none_format():
    call = DatabasesGetCall(data_format=None)
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_html_format():
    call = DatabasesGetCall(data_format="html")
    assert {
        "accept": "text/html"
    } == call.headers()


def test_headers_for_xml_format():
    call = DatabasesGetCall(data_format="xml")
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_json_format():
    call = DatabasesGetCall(data_format="json")
    assert {
        "accept": "application/json"
    } == call.headers()


def test_body():
    assert DatabasesGetCall().body() is None


def test_fully_parametrized_call():
    call = DatabasesGetCall(data_format="json",
                            view="schema")
    assert call.method() == "GET"
    assert {
        "accept": "application/json"
    } == call.headers()
    assert {
         "format": "json",
         "view": "schema"
    } == call.params()
    assert call.body() is None
