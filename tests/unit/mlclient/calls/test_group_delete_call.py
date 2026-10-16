import pytest

from mlclient.calls import GroupDeleteCall


@pytest.fixture
def default_group_delete_call():
    """Returns a GroupDeleteCall instance"""
    return GroupDeleteCall(group="custom-group")


def test_endpoint():
    expected_id_endpoint = "/manage/v2/groups/4644221823588289107"
    expected_name_endpoint = "/manage/v2/groups/custom-group"
    assert GroupDeleteCall(group="4644221823588289107").endpoint == expected_id_endpoint
    assert GroupDeleteCall(group="custom-group").endpoint == expected_name_endpoint


def test_method(default_group_delete_call):
    assert default_group_delete_call.method == "DELETE"


def test_parameters(default_group_delete_call):
    assert default_group_delete_call.params == {}


def test_headers(default_group_delete_call):
    assert default_group_delete_call.headers == {}


def test_body(default_group_delete_call):
    assert default_group_delete_call.body is None
