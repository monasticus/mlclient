import pytest

from mlclient import exceptions
from mlclient.calls import RolesPostCall


@pytest.fixture()
def default_roles_post_call():
    """Returns an RolesPostCall instance"""
    return RolesPostCall(body={"role-name": "custom-role"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RolesPostCall(body=None)

    expected_msg = ("No request body provided for "
                    "POST /manage/v2/roles!")
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RolesPostCall(body=" \n")

    expected_msg = ("No request body provided for "
                    "POST /manage/v2/roles!")
    assert err.value.args[0] == expected_msg


def test_endpoint(default_roles_post_call):
    assert default_roles_post_call.endpoint == "/manage/v2/roles"


def test_method(default_roles_post_call):
    assert default_roles_post_call.method == "POST"


def test_parameters(default_roles_post_call):
    assert default_roles_post_call.params == {}


def test_headers_for_dict_body():
    call = RolesPostCall(body={"role-name": "custom-role"})
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = RolesPostCall(body='{"role-name": "custom-role"}')
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_xml_body():
    body = ('<role-properties xmlns="http://marklogic.com/manage/role/properties">'
            '  <role-name>custom-role</role-name>'
            '</role-properties>')
    call = RolesPostCall(body=body)
    assert call.headers == {
        "Content-Type": "application/xml",
    }


def test_dict_body():
    call = RolesPostCall(body={"role-name": "custom-role"})
    assert call.body == {"role-name": "custom-role"}


def test_stringified_dict_body():
    call = RolesPostCall(body='{"role-name": "custom-role"}')
    assert call.body == {"role-name": "custom-role"}


def test_xml_body():
    body = ('<role-properties xmlns="http://marklogic.com/manage/role/properties">'
            '  <role-name>custom-role</role-name>'
            '</role-properties>')
    call = RolesPostCall(body=body)
    assert call.body == body
