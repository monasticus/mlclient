import pytest

from mlclient import exceptions
from mlclient.calls import RequestGetCall


@pytest.fixture
def default_request_get_call():
    """Returns a RequestGetCall instance"""
    return RequestGetCall(request="3420663636851293586")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RequestGetCall(request="3420663636851293586", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_request_get_call):
    expected_endpoint = "/manage/v2/requests/3420663636851293586"
    assert default_request_get_call.endpoint == expected_endpoint


def test_method(default_request_get_call):
    assert default_request_get_call.method == "GET"


def test_params(default_request_get_call):
    assert default_request_get_call.params == {
        "format": "xml",
    }


def test_headers(default_request_get_call):
    assert default_request_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = RequestGetCall(request="3420663636851293586", data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = RequestGetCall(request="3420663636851293586", data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_json_format():
    call = RequestGetCall(request="3420663636851293586", data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_request_get_call):
    assert default_request_get_call.body is None


def test_fully_parametrized_call():
    call = RequestGetCall(
        request="3420663636851293586",
        data_format="json",
        group_id="Default",
        host_id="ml-host.example.com",
        server_id="App-Services",
    )
    assert call.method == "GET"
    assert call.endpoint == "/manage/v2/requests/3420663636851293586"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "group-id": "Default",
        "host-id": "ml-host.example.com",
        "server-id": "App-Services",
    }
    assert call.body is None
