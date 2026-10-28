import pytest

from mlclient import exceptions
from mlclient.calls import GroupsPostCall


@pytest.fixture
def default_groups_post_call():
    """Returns a GroupsPostCall instance"""
    return GroupsPostCall(body={"group-name": "custom-group"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupsPostCall(body=None)

    expected_msg = "No request body provided for POST /manage/v2/groups!"
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupsPostCall(body=" \n")

    expected_msg = "No request body provided for POST /manage/v2/groups!"
    assert err.value.args[0] == expected_msg


def test_validation_json_array_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupsPostCall(body='[{"group-name": "custom-group"}]')

    expected_msg = "POST /manage/v2/groups requires a JSON object or XML body"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_groups_post_call):
    assert default_groups_post_call.endpoint == "/manage/v2/groups"


def test_method(default_groups_post_call):
    assert default_groups_post_call.method == "POST"


def test_parameters(default_groups_post_call):
    assert default_groups_post_call.params == {}


def test_headers_for_dict_body():
    call = GroupsPostCall(body={"group-name": "custom-group"})
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = GroupsPostCall(body='{"group-name": "custom-group"}')
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_xml_body():
    body = (
        '<group-properties xmlns="http://marklogic.com/manage">'
        "  <group-name>custom-group</group-name>"
        "</group-properties>"
    )
    call = GroupsPostCall(body=body)
    assert call.headers == {
        "Content-Type": "application/xml",
    }


def test_dict_body():
    call = GroupsPostCall(body={"group-name": "custom-group"})
    assert call.body == {"group-name": "custom-group"}


def test_stringified_dict_body():
    call = GroupsPostCall(body='{"group-name": "custom-group"}')
    assert call.body == {"group-name": "custom-group"}


def test_xml_body():
    body = (
        '<group-properties xmlns="http://marklogic.com/manage">'
        "  <group-name>custom-group</group-name>"
        "</group-properties>"
    )
    call = GroupsPostCall(body=body)
    assert call.body == (
        '<group-properties xmlns="http://marklogic.com/manage">'
        "  <group-name>custom-group</group-name>"
        "</group-properties>"
    )
