import pytest

from mlclient import exceptions
from mlclient.calls import UserGetCall


@pytest.fixture()
def default_user_get_call():
    """Returns an UserGetCall instance"""
    return UserGetCall(user="admin")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        UserGetCall(user="admin", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        UserGetCall(user="admin", view="X")

    expected_msg = "The supported views are: describe, default"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    assert UserGetCall(user="1").endpoint == "/manage/v2/users/1"
    assert UserGetCall(user="admin").endpoint == "/manage/v2/users/admin"


def test_method(default_user_get_call):
    assert default_user_get_call.method == "GET"


def test_parameters(default_user_get_call):
    assert default_user_get_call.params == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_user_get_call):
    assert default_user_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = UserGetCall(user="admin", data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = UserGetCall(user="admin", data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = UserGetCall(user="admin", data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = UserGetCall(user="admin", data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_user_get_call):
    assert default_user_get_call.body is None


def test_fully_parametrized_call():
    call = UserGetCall(user="admin",
                       data_format="json",
                       view="describe")
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "view": "describe",
    }
    assert call.body is None
