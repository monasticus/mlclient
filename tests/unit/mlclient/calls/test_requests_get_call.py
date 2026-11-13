import pytest

from mlclient import exceptions
from mlclient.calls import RequestsGetCall


@pytest.fixture
def default_requests_get_call():
    """Returns a RequestsGetCall instance"""
    return RequestsGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RequestsGetCall(data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RequestsGetCall(view="status")

    expected_msg = "The supported views are: default, schema, describe"
    assert err.value.args[0] == expected_msg


@pytest.mark.parametrize("seconds_min", [-1, 1.5, "1", True])
def test_validation_seconds_min_param(seconds_min):
    with pytest.raises(exceptions.WrongParametersError) as err:
        RequestsGetCall(seconds_min=seconds_min)

    expected_msg = "The seconds_min parameter must be a non-negative integer"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_requests_get_call):
    assert default_requests_get_call.endpoint == "/manage/v2/requests"


def test_method(default_requests_get_call):
    assert default_requests_get_call.method == "GET"


def test_params(default_requests_get_call):
    assert default_requests_get_call.params == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_requests_get_call):
    assert default_requests_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = RequestsGetCall(data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = RequestsGetCall(data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_json_format():
    call = RequestsGetCall(data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_params_for_none_view():
    assert RequestsGetCall(view=None).params["view"] == "default"


@pytest.mark.parametrize("view", ["default", "schema", "describe"])
def test_supported_views(view):
    assert RequestsGetCall(view=view).params["view"] == view


def test_body(default_requests_get_call):
    assert default_requests_get_call.body is None


def test_zero_seconds_min_is_sent():
    assert RequestsGetCall(seconds_min=0).params["seconds-min"] == "0"


@pytest.mark.parametrize(("full_refs", "expected"), [(True, "true"), (False, "false")])
def test_full_refs_param(full_refs, expected):
    assert RequestsGetCall(full_refs=full_refs).params["fullrefs"] == expected


def test_fully_parametrized_call():
    call = RequestsGetCall(
        data_format="json",
        view="default",
        group_id="Default",
        host_id="ml-host.example.com",
        server_id="App-Services",
        seconds_min=5,
        full_refs=True,
    )
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "view": "default",
        "group-id": "Default",
        "host-id": "ml-host.example.com",
        "server-id": "App-Services",
        "seconds-min": "5",
        "fullrefs": "true",
    }
    assert call.body is None
