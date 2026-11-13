import pytest

from mlclient import exceptions
from mlclient.calls import ResourcePostCall


@pytest.fixture
def default_resource_post_call():
    """Returns a ResourcePostCall instance"""
    return ResourcePostCall(name="echo")


@pytest.mark.parametrize("name", [None, "", "   "])
def test_validation_name_param(name):
    with pytest.raises(exceptions.WrongParametersError) as err:
        ResourcePostCall(name=name)

    expected_msg = "No resource name provided for /v1/resources/{name}!"
    assert str(err.value) == expected_msg


@pytest.mark.parametrize("body", ["<a/>", b"\x00\x01"])
def test_validation_body_without_content_type(body):
    with pytest.raises(exceptions.WrongParametersError) as err:
        ResourcePostCall(name="echo", body=body)

    expected_msg = "A str or bytes body requires a content_type!"
    assert str(err.value) == expected_msg


def test_validation_unsupported_body_type():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ResourcePostCall(name="echo", body=42)

    expected_msg = "The body must be a dict, list, str or bytes, got int"
    assert str(err.value) == expected_msg


def test_endpoint(default_resource_post_call):
    assert default_resource_post_call.endpoint == "/v1/resources/echo"


def test_method(default_resource_post_call):
    assert default_resource_post_call.method == "POST"


def test_parameters(default_resource_post_call):
    assert default_resource_post_call.params == {}


def test_extension_parameters_are_prefixed():
    call = ResourcePostCall(name="echo", params={"a": ["x", "y"], "rs:b": False})

    assert call.params == {"rs:a": ["x", "y"], "rs:b": "false"}


def test_headers(default_resource_post_call):
    assert default_resource_post_call.headers == {}


def test_body(default_resource_post_call):
    assert default_resource_post_call.body is None


def test_dict_body():
    call = ResourcePostCall(name="echo", body={"k": 1})

    assert call.headers == {"Content-Type": "application/json"}
    assert call.body == '{"k": 1}'


def test_list_body():
    call = ResourcePostCall(name="echo", body=[{"k": 1}, 2])

    assert call.headers == {"Content-Type": "application/json"}
    assert call.body == '[{"k": 1}, 2]'


def test_dict_body_with_explicit_content_type():
    call = ResourcePostCall(
        name="echo",
        body={"k": 1},
        content_type="application/vnd.example+json",
    )

    assert call.headers == {"Content-Type": "application/vnd.example+json"}
    assert call.body == '{"k": 1}'


def test_str_body():
    call = ResourcePostCall(name="echo", body="<a/>", content_type="application/xml")

    assert call.headers == {"Content-Type": "application/xml"}
    assert call.body == "<a/>"


def test_bytes_body():
    call = ResourcePostCall(
        name="echo",
        body=b"\x00\x01",
        content_type="application/octet-stream",
    )

    assert call.headers == {"Content-Type": "application/octet-stream"}
    assert call.body == b"\x00\x01"


def test_fully_parametrized_call():
    call = ResourcePostCall(
        name="echo",
        params={"a": "x"},
        body="hello",
        content_type="text/plain",
        database="Documents",
        txid="12345",
        accept="application/json",
    )
    assert call.method == "POST"
    assert call.endpoint == "/v1/resources/echo"
    assert call.headers == {
        "Accept": "application/json",
        "Content-Type": "text/plain",
    }
    assert call.params == {
        "rs:a": "x",
        "database": "Documents",
        "txid": "12345",
    }
    assert call.body == "hello"
