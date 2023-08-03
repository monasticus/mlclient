import pytest

from mlclient import exceptions
from mlclient.calls import UserPropertiesPutCall


@pytest.fixture()
def default_user_properties_put_call():
    """Returns an UserPropertiesPutCall instance"""
    return UserPropertiesPutCall(user="admin", body={"user-name": "custom-user"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        UserPropertiesPutCall(user="admin", body=None)

    expected_msg = ("No request body provided for "
                    "PUT /manage/v2/users/{id|name}/properties!")
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        UserPropertiesPutCall(user="admin", body=" \n")

    expected_msg = ("No request body provided for "
                    "PUT /manage/v2/users/{id|name}/properties!")
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/users/1/properties"
    expected__name_endpoint = "/manage/v2/users/admin/properties"
    assert UserPropertiesPutCall(
        user="1",
        body={"user-name": "custom-user"}).endpoint() == expected__id_endpoint
    assert UserPropertiesPutCall(
        user="admin",
        body={"user-name": "custom-user"}).endpoint() == expected__name_endpoint


def test_method(default_user_properties_put_call):
    assert default_user_properties_put_call.method == "PUT"


def test_parameters(default_user_properties_put_call):
    assert default_user_properties_put_call.params == {}


def test_headers_for_dict_body():
    call = UserPropertiesPutCall(user="admin", body={"user-name": "custom-user"})
    assert call.headers == {
        "content-type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = UserPropertiesPutCall(user="admin", body='{"user-name": "custom-user"}')
    assert call.headers == {
        "content-type": "application/json",
    }


def test_headers_for_xml_body():
    body = ('<user-properties xmlns="http://marklogic.com/manage/user/properties">'
            '  <user-name>custom-user</user-name>'
            '</user-properties>')
    call = UserPropertiesPutCall(user="admin", body=body)
    assert call.headers == {
        "content-type": "application/xml",
    }


def test_dict_body():
    call = UserPropertiesPutCall(user="admin", body={"user-name": "custom-user"})
    assert call.body == {"user-name": "custom-user"}


def test_stringified_dict_body():
    call = UserPropertiesPutCall(user="admin", body='{"user-name": "custom-user"}')
    assert call.body == {"user-name": "custom-user"}


def test_xml_body():
    body = ('<user-properties xmlns="http://marklogic.com/manage/user/properties">'
            '  <user-name>custom-user</user-name>'
            '</user-properties>')
    call = UserPropertiesPutCall(user="admin", body=body)
    assert call.body == body
