import pytest

from mlclient import exceptions
from mlclient.calls import RoleGetCall


@pytest.fixture()
def default_role_get_call():
    """Returns an RoleGetCall instance"""
    return RoleGetCall(role="admin")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RoleGetCall(role="admin", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        RoleGetCall(role="admin", view="X")

    expected_msg = "The supported views are: describe, default"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    assert RoleGetCall(role="1").endpoint == "/manage/v2/roles/1"
    assert RoleGetCall(role="admin").endpoint == "/manage/v2/roles/admin"


def test_method(default_role_get_call):
    assert default_role_get_call.method == "GET"


def test_parameters(default_role_get_call):
    assert default_role_get_call.params == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_role_get_call):
    assert default_role_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = RoleGetCall(role="admin", data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = RoleGetCall(role="admin", data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = RoleGetCall(role="admin", data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = RoleGetCall(role="admin", data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_role_get_call):
    assert default_role_get_call.body is None


def test_fully_parametrized_call():
    call = RoleGetCall(role="admin", data_format="json", view="describe")
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "view": "describe",
    }
    assert call.body is None
