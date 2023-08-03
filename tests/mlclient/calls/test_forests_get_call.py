import pytest

from mlclient import exceptions
from mlclient.calls import ForestsGetCall


@pytest.fixture()
def default_forests_get_call():
    """Returns a ForestsGetCall instance"""
    return ForestsGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestsGetCall(data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestsGetCall(view="X")

    expected_msg = ("The supported views are: "
                    "describe, default, status, metrics, "
                    "schema, storage, properties-schema")
    assert err.value.args[0] == expected_msg


def test_endpoint(default_forests_get_call):
    assert default_forests_get_call.endpoint() == "/manage/v2/forests"
    assert default_forests_get_call.ENDPOINT == "/manage/v2/forests"
    assert ForestsGetCall.ENDPOINT == "/manage/v2/forests"


def test_method(default_forests_get_call):
    assert default_forests_get_call.method == "GET"


def test_params(default_forests_get_call):
    assert default_forests_get_call.params == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_forests_get_call):
    assert default_forests_get_call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_none_format():
    call = ForestsGetCall(data_format=None)
    assert call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_html_format():
    call = ForestsGetCall(data_format="html")
    assert call.headers == {
        "accept": "text/html",
    }


def test_headers_for_xml_format():
    call = ForestsGetCall(data_format="xml")
    assert call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_json_format():
    call = ForestsGetCall(data_format="json")
    assert call.headers == {
        "accept": "application/json",
    }


def test_body(default_forests_get_call):
    assert default_forests_get_call.body is None


def test_fully_parametrized_call():
    call = ForestsGetCall(data_format="json",
                          view="schema",
                          database="Documents",
                          group="Default",
                          host="localhost",
                          full_refs=False)
    assert call.method == "GET"
    assert call.headers == {
        "accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "view": "schema",
        "database-id": "Documents",
        "group-id": "Default",
        "host-id": "localhost",
        "fullrefs": "false",
    }
    assert call.body is None
