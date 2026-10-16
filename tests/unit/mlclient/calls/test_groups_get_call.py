import pytest

from mlclient import exceptions
from mlclient.calls import GroupsGetCall


@pytest.fixture
def default_groups_get_call():
    """Returns a GroupsGetCall instance"""
    return GroupsGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupsGetCall(data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupsGetCall(view="properties-schema")

    expected_msg = "The supported views are: describe, default, schema"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_groups_get_call):
    assert default_groups_get_call.endpoint == "/manage/v2/groups"


def test_method(default_groups_get_call):
    assert default_groups_get_call.method == "GET"


def test_parameters(default_groups_get_call):
    assert default_groups_get_call.params == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_groups_get_call):
    assert default_groups_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = GroupsGetCall(data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = GroupsGetCall(data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = GroupsGetCall(data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = GroupsGetCall(data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_parameters_for_none_view():
    call = GroupsGetCall(view=None)
    assert call.params == {
        "format": "xml",
        "view": "default",
    }


def test_body(default_groups_get_call):
    assert default_groups_get_call.body is None


def test_fully_parametrized_call():
    call = GroupsGetCall(data_format="json", view="describe")
    assert call.method == "GET"
    assert call.endpoint == "/manage/v2/groups"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "view": "describe",
    }
    assert call.body is None
