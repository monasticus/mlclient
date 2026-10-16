import pytest

from mlclient import exceptions
from mlclient.calls import HostPropertiesPutCall


@pytest.fixture
def default_host_properties_put_call():
    """Returns a HostPropertiesPutCall instance"""
    return HostPropertiesPutCall(host="ml-host.example.com", body={"zone": "zone-a"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostPropertiesPutCall(host="ml-host.example.com", body=None)

    expected_msg = (
        "No request body provided for PUT /manage/v2/hosts/{id|name}/properties!"
    )
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostPropertiesPutCall(host="ml-host.example.com", body=" \n")

    expected_msg = (
        "No request body provided for PUT /manage/v2/hosts/{id|name}/properties!"
    )
    assert err.value.args[0] == expected_msg


def test_validation_json_array_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostPropertiesPutCall(host="ml-host.example.com", body='[{"zone": "zone-a"}]')

    expected_msg = (
        "PUT /manage/v2/hosts/{id|name}/properties requires a JSON object or XML body"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint():
    body = {"zone": "zone-a"}
    expected_id_endpoint = "/manage/v2/hosts/13544732455686476949/properties"
    expected_name_endpoint = "/manage/v2/hosts/ml-host.example.com/properties"
    assert (
        HostPropertiesPutCall(host="13544732455686476949", body=body).endpoint
        == expected_id_endpoint
    )
    assert (
        HostPropertiesPutCall(host="ml-host.example.com", body=body).endpoint
        == expected_name_endpoint
    )


def test_method(default_host_properties_put_call):
    assert default_host_properties_put_call.method == "PUT"


def test_parameters(default_host_properties_put_call):
    assert default_host_properties_put_call.params == {}


def test_headers_for_dict_body():
    call = HostPropertiesPutCall(host="ml-host.example.com", body={"zone": "zone-a"})
    assert call.headers == {"Content-Type": "application/json"}


def test_headers_for_stringified_dict_body():
    call = HostPropertiesPutCall(host="ml-host.example.com", body='{"zone": "zone-a"}')
    assert call.headers == {"Content-Type": "application/json"}


def test_headers_for_xml_body():
    body = (
        '<host-properties xmlns="http://marklogic.com/manage">'
        "  <zone>zone-a</zone>"
        "</host-properties>"
    )
    call = HostPropertiesPutCall(host="ml-host.example.com", body=body)
    assert call.headers == {"Content-Type": "application/xml"}


def test_dict_body():
    call = HostPropertiesPutCall(host="ml-host.example.com", body={"zone": "zone-a"})
    assert call.body == {"zone": "zone-a"}


def test_stringified_dict_body():
    call = HostPropertiesPutCall(host="ml-host.example.com", body='{"zone": "zone-a"}')
    assert call.body == {"zone": "zone-a"}


def test_xml_body():
    body = (
        '<host-properties xmlns="http://marklogic.com/manage">'
        "  <zone>zone-a</zone>"
        "</host-properties>"
    )
    call = HostPropertiesPutCall(host="ml-host.example.com", body=body)
    assert call.body == (
        '<host-properties xmlns="http://marklogic.com/manage">'
        "  <zone>zone-a</zone>"
        "</host-properties>"
    )
