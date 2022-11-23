import pytest

from mlclient.calls import UserDeleteCall


@pytest.fixture
def default_user_delete_call():
    """Returns an UserDeleteCall instance"""
    return UserDeleteCall(user="admin")


def test_endpoint(default_user_delete_call):
    assert UserDeleteCall(user="1").endpoint() == "/manage/v2/users/1"
    assert UserDeleteCall(user="admin").endpoint() == "/manage/v2/users/admin"


def test_method(default_user_delete_call):
    assert default_user_delete_call.method() == "DELETE"


def test_parameters(default_user_delete_call):
    assert default_user_delete_call.params() == {}


def test_headers(default_user_delete_call):
    assert default_user_delete_call.headers() == {}


def test_body(default_user_delete_call):
    assert default_user_delete_call.body() is None
