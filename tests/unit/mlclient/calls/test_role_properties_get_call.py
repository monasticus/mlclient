import pytest

from mlclient import exceptions
from mlclient.calls import RolePropertiesGetCall


@pytest.fixture()
def default_role_properties_get_call():
    """Returns an RolePropertiesGetCall instance"""
    return RolePropertiesGetCall(role="admin")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RolePropertiesGetCall(role="admin", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/roles/1/properties"
    expected__name_endpoint = "/manage/v2/roles/admin/properties"
    assert RolePropertiesGetCall(role="1").endpoint == expected__id_endpoint
    assert RolePropertiesGetCall(role="admin").endpoint == expected__name_endpoint


def test_method(default_role_properties_get_call):
    assert default_role_properties_get_call.method == "GET"


def test_parameters(default_role_properties_get_call):
    assert default_role_properties_get_call.params == {
        "format": "xml",
    }


def test_headers(default_role_properties_get_call):
    assert default_role_properties_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = RolePropertiesGetCall(role="admin", data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = RolePropertiesGetCall(role="admin", data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = RolePropertiesGetCall(role="admin", data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = RolePropertiesGetCall(role="admin", data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_role_properties_get_call):
    assert default_role_properties_get_call.body is None
