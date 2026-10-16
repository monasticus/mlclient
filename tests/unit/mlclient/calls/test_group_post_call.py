import pytest

from mlclient import exceptions
from mlclient.calls import GroupPostCall


@pytest.fixture
def default_group_post_call():
    """Returns a GroupPostCall instance"""
    return GroupPostCall(group="Default", body={"operation": "restart-group"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupPostCall(group="Default", body=None)

    expected_msg = "No request body provided for POST /manage/v2/groups/{id|name}!"
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupPostCall(group="Default", body=" \n")

    expected_msg = "No request body provided for POST /manage/v2/groups/{id|name}!"
    assert err.value.args[0] == expected_msg


def test_validation_json_array_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupPostCall(group="Default", body='[{"operation": "restart-group"}]')

    expected_msg = "POST /manage/v2/groups/{id|name} requires a JSON object or XML body"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    body = {"operation": "restart-group"}
    expected_id_endpoint = "/manage/v2/groups/4644221823588289107"
    expected_name_endpoint = "/manage/v2/groups/Default"
    assert (
        GroupPostCall(group="4644221823588289107", body=body).endpoint
        == expected_id_endpoint
    )
    assert GroupPostCall(group="Default", body=body).endpoint == expected_name_endpoint


def test_method(default_group_post_call):
    assert default_group_post_call.method == "POST"


def test_parameters(default_group_post_call):
    assert default_group_post_call.params == {}


def test_headers_for_dict_body():
    call = GroupPostCall(group="Default", body={"operation": "restart-group"})
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = GroupPostCall(group="Default", body='{"operation": "restart-group"}')
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_xml_body():
    body = (
        '<restart-group-operation xmlns="http://marklogic.com/manage">'
        "</restart-group-operation>"
    )
    call = GroupPostCall(group="Default", body=body)
    assert call.headers == {
        "Content-Type": "application/xml",
    }


def test_dict_body():
    call = GroupPostCall(group="Default", body={"operation": "shutdown-group"})
    assert call.body == {"operation": "shutdown-group"}


def test_stringified_dict_body():
    call = GroupPostCall(group="Default", body='{"operation": "shutdown-group"}')
    assert call.body == {"operation": "shutdown-group"}


def test_xml_body():
    body = (
        '<restart-group-operation xmlns="http://marklogic.com/manage">'
        "</restart-group-operation>"
    )
    call = GroupPostCall(group="Default", body=body)
    assert call.body == (
        '<restart-group-operation xmlns="http://marklogic.com/manage">'
        "</restart-group-operation>"
    )
