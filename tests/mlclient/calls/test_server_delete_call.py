import pytest

from mlclient.calls import ServerDeleteCall


@pytest.fixture()
def default_server_delete_call():
    """Returns an ServerDeleteCall instance"""
    return ServerDeleteCall(
        server="App-Services",
        group_id="Default")


def test_endpoint():
    assert ServerDeleteCall(
        server="1",
        group_id="Default").endpoint() == "/manage/v2/servers/1"
    assert ServerDeleteCall(
        server="App-Services",
        group_id="Default").endpoint() == "/manage/v2/servers/App-Services"


def test_method(default_server_delete_call):
    assert default_server_delete_call.method == "DELETE"


def test_parameters(default_server_delete_call):
    assert default_server_delete_call.params == {
        "group-id": "Default",
    }


def test_headers(default_server_delete_call):
    assert default_server_delete_call.headers == {}


def test_body(default_server_delete_call):
    assert default_server_delete_call.body is None


def test_fully_parametrized_call():
    call = ServerDeleteCall(
        server="App-Services",
        group_id="Default")
    assert call.method == "DELETE"
    assert call.headers == {}
    assert call.params == {
        "group-id": "Default",
    }
    assert call.body is None
