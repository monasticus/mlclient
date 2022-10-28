import pytest

from mlclient import exceptions
from mlclient.calls.managementapi import DatabasesCall


@pytest.fixture
def default_databases_call():
    """Returns an DatabasesCall instance"""
    return DatabasesCall(method="GET")


def test_validation_method_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasesCall(method="PUT")

    assert err.value.args[0] == "Method not allowed: the supported methods are GET and POST!"


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasesCall(method="GET", resp_format="text")

    assert err.value.args[0] == "The supported formats are: xml, json, html"


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasesCall(method="GET", view="X")

    assert err.value.args[0] == "The supported views are: " \
                                "describe, default, metrics, package, schema, properties-schema"


def test_endpoint(default_databases_call):
    assert default_databases_call.endpoint() == "/manage/v2/databases"
    assert default_databases_call.ENDPOINT == "/manage/v2/databases"
    assert DatabasesCall.ENDPOINT == "/manage/v2/databases"


def test_method():
    assert DatabasesCall(method="GET").method() == "GET"
    assert DatabasesCall(method="POST").method() == "POST"


def test_headers_for_default_format():
    call = DatabasesCall(method="GET")
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_none_format():
    call = DatabasesCall(method="GET", resp_format=None)
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_html_format():
    call = DatabasesCall(method="GET", resp_format="html")
    assert {
        "accept": "text/html"
    } == call.headers()


def test_headers_for_xml_format():
    call = DatabasesCall(method="GET", resp_format="xml")
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_json_format():
    call = DatabasesCall(method="GET", resp_format="json")
    assert {
        "accept": "application/json"
    } == call.headers()


def test_body_for_get_request():
    assert DatabasesCall(method="GET").body() is None


def test_fully_parametrized_get_call():
    call = DatabasesCall(method="GET",
                         resp_format="json",
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
