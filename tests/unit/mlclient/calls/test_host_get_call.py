import pytest

from mlclient import exceptions
from mlclient.calls import HostGetCall


@pytest.fixture
def default_host_get_call():
    """Returns a HostGetCall instance"""
    return HostGetCall(host="ml-host.example.com")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostGetCall(host="ml-host.example.com", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostGetCall(host="ml-host.example.com", view="metrics")

    expected_msg = (
        "The supported views are: "
        "describe, default, config, counts, edit, status, properties-schema"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected_id_endpoint = "/manage/v2/hosts/13544732455686476949"
    expected_name_endpoint = "/manage/v2/hosts/ml-host.example.com"
    assert HostGetCall(host="13544732455686476949").endpoint == expected_id_endpoint
    assert HostGetCall(host="ml-host.example.com").endpoint == expected_name_endpoint


def test_method(default_host_get_call):
    assert default_host_get_call.method == "GET"


def test_parameters(default_host_get_call):
    assert default_host_get_call.params == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_host_get_call):
    assert default_host_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = HostGetCall(host="ml-host.example.com", data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = HostGetCall(host="ml-host.example.com", data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = HostGetCall(host="ml-host.example.com", data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = HostGetCall(host="ml-host.example.com", data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_parameters_for_none_view():
    call = HostGetCall(host="ml-host.example.com", view=None)
    assert call.params == {
        "format": "xml",
        "view": "default",
    }


def test_body(default_host_get_call):
    assert default_host_get_call.body is None


def test_fully_parametrized_call():
    call = HostGetCall(host="ml-host.example.com", data_format="json", view="counts")
    assert call.method == "GET"
    assert call.endpoint == "/manage/v2/hosts/ml-host.example.com"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "view": "counts",
    }
    assert call.body is None
