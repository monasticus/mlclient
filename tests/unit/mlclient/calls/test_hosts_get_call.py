import pytest

from mlclient import exceptions
from mlclient.calls import HostsGetCall


@pytest.fixture
def default_hosts_get_call():
    """Returns a HostsGetCall instance"""
    return HostsGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostsGetCall(data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostsGetCall(view="X")

    expected_msg = (
        "The supported views are: "
        "default, status, metrics, schema, properties-schema, describe"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint(default_hosts_get_call):
    assert default_hosts_get_call.endpoint == "/manage/v2/hosts"


def test_method(default_hosts_get_call):
    assert default_hosts_get_call.method == "GET"


def test_params(default_hosts_get_call):
    assert default_hosts_get_call.params == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_hosts_get_call):
    assert default_hosts_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = HostsGetCall(data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = HostsGetCall(data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = HostsGetCall(data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = HostsGetCall(data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_hosts_get_call):
    assert default_hosts_get_call.body is None


def test_fully_parametrized_call():
    call = HostsGetCall(
        data_format="json",
        group_id="Default",
        view="status",
    )
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "group-id": "Default",
        "view": "status",
    }
    assert call.body is None


def test_schema_view():
    assert HostsGetCall(view="schema").params["view"] == "schema"
