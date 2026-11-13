import pytest

from mlclient import exceptions
from mlclient.calls import ResourceDeleteCall


@pytest.fixture
def default_resource_delete_call():
    """Returns a ResourceDeleteCall instance"""
    return ResourceDeleteCall(name="echo")


@pytest.mark.parametrize("name", [None, "", "   "])
def test_validation_name_param(name):
    with pytest.raises(exceptions.WrongParametersError) as err:
        ResourceDeleteCall(name=name)

    expected_msg = "No resource name provided for /v1/resources/{name}!"
    assert str(err.value) == expected_msg


def test_endpoint(default_resource_delete_call):
    assert default_resource_delete_call.endpoint == "/v1/resources/echo"


def test_endpoint_with_a_name_needing_encoding():
    call = ResourceDeleteCall(name="my echo/v2")

    assert call.endpoint == "/v1/resources/my%20echo%2Fv2"


def test_method(default_resource_delete_call):
    assert default_resource_delete_call.method == "DELETE"


def test_parameters(default_resource_delete_call):
    assert default_resource_delete_call.params == {}


def test_extension_parameters_are_prefixed():
    call = ResourceDeleteCall(
        name="echo",
        params={"a": "x", "rs:b": "y", "c": ["1", "2"], "flag": True, "n": 3},
    )

    assert call.params == {
        "rs:a": "x",
        "rs:b": "y",
        "rs:c": ["1", "2"],
        "rs:flag": "true",
        "rs:n": "3",
    }


def test_headers(default_resource_delete_call):
    assert default_resource_delete_call.headers == {}


def test_body(default_resource_delete_call):
    assert default_resource_delete_call.body is None


def test_fully_parametrized_call():
    call = ResourceDeleteCall(
        name="echo",
        params={"a": "x"},
        database="Documents",
        txid="12345",
        accept="application/json",
    )
    assert call.method == "DELETE"
    assert call.endpoint == "/v1/resources/echo"
    assert call.headers == {"Accept": "application/json"}
    assert call.params == {
        "rs:a": "x",
        "database": "Documents",
        "txid": "12345",
    }
    assert call.body is None
