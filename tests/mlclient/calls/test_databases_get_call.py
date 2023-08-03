import pytest

from mlclient import exceptions
from mlclient.calls import DatabasesGetCall


@pytest.fixture()
def default_databases_get_call():
    """Returns an DatabasesGetCall instance"""
    return DatabasesGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DatabasesGetCall(data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DatabasesGetCall(view="X")

    expected_msg = ("The supported views are: "
                    "describe, default, metrics, package, schema, properties-schema")
    assert err.value.args[0] == expected_msg


def test_endpoint(default_databases_get_call):
    assert default_databases_get_call.endpoint == "/manage/v2/databases"
    assert default_databases_get_call.ENDPOINT == "/manage/v2/databases"
    assert DatabasesGetCall.ENDPOINT == "/manage/v2/databases"


def test_method(default_databases_get_call):
    assert default_databases_get_call.method == "GET"


def test_parameters(default_databases_get_call):
    assert default_databases_get_call.params == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_databases_get_call):
    assert default_databases_get_call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_none_format():
    call = DatabasesGetCall(data_format=None)
    assert call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_html_format():
    call = DatabasesGetCall(data_format="html")
    assert call.headers == {
        "accept": "text/html",
    }


def test_headers_for_xml_format():
    call = DatabasesGetCall(data_format="xml")
    assert call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_json_format():
    call = DatabasesGetCall(data_format="json")
    assert call.headers == {
        "accept": "application/json",
    }


def test_body(default_databases_get_call):
    assert default_databases_get_call.body is None


def test_fully_parametrized_call():
    call = DatabasesGetCall(data_format="json",
                            view="schema")
    assert call.method == "GET"
    assert call.headers == {
        "accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "view": "schema",
    }
    assert call.body is None
