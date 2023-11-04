import pytest

from mlclient import exceptions
from mlclient.calls import RolePropertiesPutCall


@pytest.fixture()
def default_role_properties_put_call():
    """Returns an RolePropertiesPutCall instance"""
    return RolePropertiesPutCall(role="admin", body={"role-name": "custom-role"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RolePropertiesPutCall(role="admin", body=None)

    expected_msg = (
        "No request body provided for PUT /manage/v2/roles/{id|name}/properties!"
    )
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RolePropertiesPutCall(role="admin", body=" \n")

    expected_msg = (
        "No request body provided for PUT /manage/v2/roles/{id|name}/properties!"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/roles/1/properties"
    expected__name_endpoint = "/manage/v2/roles/admin/properties"
    assert (
        RolePropertiesPutCall(role="1", body={"role-name": "custom-role"}).endpoint
        == expected__id_endpoint
    )
    assert (
        RolePropertiesPutCall(role="admin", body={"role-name": "custom-role"}).endpoint
        == expected__name_endpoint
    )


def test_method(default_role_properties_put_call):
    assert default_role_properties_put_call.method == "PUT"


def test_parameters(default_role_properties_put_call):
    assert default_role_properties_put_call.params == {}


def test_headers_for_dict_body():
    call = RolePropertiesPutCall(role="admin", body={"role-name": "custom-role"})
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = RolePropertiesPutCall(role="admin", body='{"role-name": "custom-role"}')
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_xml_body():
    body = (
        '<role-properties xmlns="http://marklogic.com/manage/role/properties">'
        "  <role-name>custom-role</role-name>"
        "</role-properties>"
    )
    call = RolePropertiesPutCall(role="admin", body=body)
    assert call.headers == {
        "Content-Type": "application/xml",
    }


def test_dict_body():
    call = RolePropertiesPutCall(role="admin", body={"role-name": "custom-role"})
    assert call.body == {"role-name": "custom-role"}


def test_stringified_dict_body():
    call = RolePropertiesPutCall(role="admin", body='{"role-name": "custom-role"}')
    assert call.body == {"role-name": "custom-role"}


def test_xml_body():
    body = (
        '<role-properties xmlns="http://marklogic.com/manage/role/properties">'
        "  <role-name>custom-role</role-name>"
        "</role-properties>"
    )
    call = RolePropertiesPutCall(role="admin", body=body)
    assert call.body == body
