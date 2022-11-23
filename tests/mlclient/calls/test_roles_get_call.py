import pytest

from mlclient import exceptions
from mlclient.calls import RolesGetCall


@pytest.fixture
def default_roles_get_call():
    """Returns an RolesGetCall instance"""
    return RolesGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        RolesGetCall(data_format="text")

    assert err.value.args[0] == "The supported formats are: xml, json, html"


def test_endpoint(default_roles_get_call):
    assert default_roles_get_call.endpoint() == "/manage/v2/roles"
    assert default_roles_get_call.ENDPOINT == "/manage/v2/roles"
    assert RolesGetCall.ENDPOINT == "/manage/v2/roles"


def test_method(default_roles_get_call):
    assert default_roles_get_call.method() == "GET"


def test_parameters(default_roles_get_call):
    assert default_roles_get_call.params() == {
        "format": "xml"
    }


def test_headers(default_roles_get_call):
    assert default_roles_get_call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_none_format():
    call = RolesGetCall(data_format=None)
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_html_format():
    call = RolesGetCall(data_format="html")
    assert call.headers() == {
        "accept": "text/html"
    }


def test_headers_for_xml_format():
    call = RolesGetCall(data_format="xml")
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_json_format():
    call = RolesGetCall(data_format="json")
    assert call.headers() == {
        "accept": "application/json"
    }


def test_body(default_roles_get_call):
    assert default_roles_get_call.body() is None
