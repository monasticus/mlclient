import pytest

from mlclient import exceptions
from mlclient.calls import UserPropertiesGetCall


@pytest.fixture
def default_user_properties_get_call():
    """Returns an UserPropertiesGetCall instance"""
    return UserPropertiesGetCall(user="admin")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        UserPropertiesGetCall(user="admin", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/users/1/properties"
    expected__name_endpoint = "/manage/v2/users/admin/properties"
    assert UserPropertiesGetCall(user="1").endpoint() == expected__id_endpoint
    assert UserPropertiesGetCall(user="admin").endpoint() == expected__name_endpoint


def test_method(default_user_properties_get_call):
    assert default_user_properties_get_call.method() == "GET"


def test_parameters(default_user_properties_get_call):
    assert default_user_properties_get_call.params() == {
        "format": "xml"
    }


def test_headers(default_user_properties_get_call):
    assert default_user_properties_get_call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_none_format():
    call = UserPropertiesGetCall(user="admin", data_format=None)
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_html_format():
    call = UserPropertiesGetCall(user="admin", data_format="html")
    assert call.headers() == {
        "accept": "text/html"
    }


def test_headers_for_xml_format():
    call = UserPropertiesGetCall(user="admin", data_format="xml")
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_json_format():
    call = UserPropertiesGetCall(user="admin", data_format="json")
    assert call.headers() == {
        "accept": "application/json"
    }


def test_body(default_user_properties_get_call):
    assert default_user_properties_get_call.body() is None
