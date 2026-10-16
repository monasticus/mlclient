import pytest

from mlclient import exceptions
from mlclient.calls import ApiCall, InstanceAdminPostCall

ADMIN_DICT = {"admin-username": "admin", "admin-password": "admin-password"}
ADMIN_JSON = '{"admin-username": "admin", "admin-password": "admin-password"}'
ADMIN_XML = (
    '<instance-admin xmlns="http://marklogic.com/manage">'
    "<admin-username>admin</admin-username>"
    "<admin-password>admin-password</admin-password>"
    "</instance-admin>"
)


@pytest.fixture
def default_instance_admin_post_call():
    """Returns an InstanceAdminPostCall instance"""
    return InstanceAdminPostCall(body=ADMIN_DICT)


def test_is_api_call():
    assert issubclass(InstanceAdminPostCall, ApiCall)


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        InstanceAdminPostCall(body=None)

    expected_msg = "No request body provided for POST /admin/v1/instance-admin!"
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        InstanceAdminPostCall(body=" \n")

    expected_msg = "No request body provided for POST /admin/v1/instance-admin!"
    assert err.value.args[0] == expected_msg


def test_validation_json_array_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        InstanceAdminPostCall(body="[1]")

    expected_msg = "POST /admin/v1/instance-admin requires a JSON object or XML body"
    assert err.value.args[0] == expected_msg


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        InstanceAdminPostCall(body=ADMIN_DICT, data_format="html")

    expected_msg = "The supported formats are: xml, json"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_instance_admin_post_call):
    assert default_instance_admin_post_call.endpoint == "/admin/v1/instance-admin"


def test_method(default_instance_admin_post_call):
    assert default_instance_admin_post_call.method == "POST"


def test_parameters(default_instance_admin_post_call):
    assert default_instance_admin_post_call.params == {}


def test_headers_for_none_format():
    call = InstanceAdminPostCall(body=ADMIN_DICT, data_format=None)
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_xml_format():
    call = InstanceAdminPostCall(body=ADMIN_DICT, data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
        "Content-Type": "application/json",
    }


def test_headers_for_json_format():
    call = InstanceAdminPostCall(body=ADMIN_DICT, data_format="json")
    assert call.headers == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def test_headers_for_dict_body():
    call = InstanceAdminPostCall(body=ADMIN_DICT)
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = InstanceAdminPostCall(body=ADMIN_JSON)
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_xml_body():
    call = InstanceAdminPostCall(body=ADMIN_XML)
    assert call.headers == {
        "Content-Type": "application/xml",
    }


def test_dict_body():
    call = InstanceAdminPostCall(body=ADMIN_DICT)
    assert call.body == {"admin-username": "admin", "admin-password": "admin-password"}


def test_stringified_dict_body():
    call = InstanceAdminPostCall(body=ADMIN_JSON)
    assert call.body == {"admin-username": "admin", "admin-password": "admin-password"}


def test_xml_body():
    call = InstanceAdminPostCall(body=ADMIN_XML)
    assert call.body == (
        '<instance-admin xmlns="http://marklogic.com/manage">'
        "<admin-username>admin</admin-username>"
        "<admin-password>admin-password</admin-password>"
        "</instance-admin>"
    )


def test_fully_parametrized_call():
    body = {
        "admin-username": "admin",
        "admin-password": "admin-password",
        "wallet-password": "wallet-password",
        "realm": "public",
    }
    call = InstanceAdminPostCall(body=body, data_format="json")
    assert call.method == "POST"
    assert call.endpoint == "/admin/v1/instance-admin"
    assert call.headers == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    assert call.params == {"format": "json"}
    assert call.body == {
        "admin-username": "admin",
        "admin-password": "admin-password",
        "wallet-password": "wallet-password",
        "realm": "public",
    }
