import pytest

from mlclient import exceptions
from mlclient.calls import HostPropertiesGetCall


@pytest.fixture
def default_host_properties_get_call():
    """Returns a HostPropertiesGetCall instance"""
    return HostPropertiesGetCall(host="ml-host.example.com")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostPropertiesGetCall(host="ml-host.example.com", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected_id_endpoint = "/manage/v2/hosts/13544732455686476949/properties"
    expected_name_endpoint = "/manage/v2/hosts/ml-host.example.com/properties"
    assert (
        HostPropertiesGetCall(host="13544732455686476949").endpoint
        == expected_id_endpoint
    )
    assert (
        HostPropertiesGetCall(host="ml-host.example.com").endpoint
        == expected_name_endpoint
    )


def test_method(default_host_properties_get_call):
    assert default_host_properties_get_call.method == "GET"


def test_parameters(default_host_properties_get_call):
    assert default_host_properties_get_call.params == {
        "format": "xml",
    }


def test_headers(default_host_properties_get_call):
    assert default_host_properties_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = HostPropertiesGetCall(host="ml-host.example.com", data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = HostPropertiesGetCall(host="ml-host.example.com", data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = HostPropertiesGetCall(host="ml-host.example.com", data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = HostPropertiesGetCall(host="ml-host.example.com", data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_host_properties_get_call):
    assert default_host_properties_get_call.body is None


def test_fully_parametrized_call():
    call = HostPropertiesGetCall(host="ml-host.example.com", data_format="json")
    assert call.method == "GET"
    assert call.endpoint == "/manage/v2/hosts/ml-host.example.com/properties"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
    }
    assert call.body is None
