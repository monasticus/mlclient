import pytest

from mlclient.calls import RoleDeleteCall


@pytest.fixture()
def default_role_delete_call():
    """Returns an RoleDeleteCall instance"""
    return RoleDeleteCall(role="admin")


def test_endpoint(default_role_delete_call):
    assert RoleDeleteCall(role="1").endpoint() == "/manage/v2/roles/1"
    assert RoleDeleteCall(role="admin").endpoint() == "/manage/v2/roles/admin"


def test_method(default_role_delete_call):
    assert default_role_delete_call.method() == "DELETE"


def test_parameters(default_role_delete_call):
    assert default_role_delete_call.params() == {}


def test_headers(default_role_delete_call):
    assert default_role_delete_call.headers() == {}


def test_body(default_role_delete_call):
    assert default_role_delete_call.body() is None
