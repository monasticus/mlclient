import pytest

from mlclient import exceptions
from mlclient.calls import UsersPostCall


@pytest.fixture()
def default_users_post_call():
    """Returns an UsersPostCall instance"""
    return UsersPostCall(body={"user-name": "custom-user"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        UsersPostCall(body=None)

    expected_msg = ("No request body provided for "
                    "POST /manage/v2/users!")
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        UsersPostCall(body=" \n")

    expected_msg = ("No request body provided for "
                    "POST /manage/v2/users!")
    assert err.value.args[0] == expected_msg


def test_endpoint(default_users_post_call):
    assert default_users_post_call.endpoint() == "/manage/v2/users"
    assert default_users_post_call.ENDPOINT == "/manage/v2/users"
    assert UsersPostCall.ENDPOINT == "/manage/v2/users"


def test_method(default_users_post_call):
    assert default_users_post_call.method() == "POST"


def test_parameters(default_users_post_call):
    assert default_users_post_call.params() == {}


def test_headers_for_dict_body():
    call = UsersPostCall(body={"user-name": "custom-user"})
    assert call.headers() == {
        "content-type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = UsersPostCall(body='{"user-name": "custom-user"}')
    assert call.headers() == {
        "content-type": "application/json",
    }


def test_headers_for_xml_body():
    body = ('<user-properties xmlns="http://marklogic.com/manage/user/properties">'
            '  <user-name>custom-user</user-name>'
            '</user-properties>')
    call = UsersPostCall(body=body)
    assert call.headers() == {
        "content-type": "application/xml",
    }


def test_dict_body():
    call = UsersPostCall(body={"user-name": "custom-user"})
    assert call.body() == {"user-name": "custom-user"}


def test_stringified_dict_body():
    call = UsersPostCall(body='{"user-name": "custom-user"}')
    assert call.body() == {"user-name": "custom-user"}


def test_xml_body():
    body = ('<user-properties xmlns="http://marklogic.com/manage/user/properties">'
            '  <user-name>custom-user</user-name>'
            '</user-properties>')
    call = UsersPostCall(body=body)
    assert call.body() == body
