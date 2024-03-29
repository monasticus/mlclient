import pytest

from mlclient import exceptions
from mlclient.calls import ForestDeleteCall


@pytest.fixture()
def default_forest_delete_call():
    """Returns an ForestDeleteCall instance"""
    return ForestDeleteCall(forest="custom-forest", level="full")


def test_validation_level_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestDeleteCall(forest="custom-forest", level="X")

    expected_msg = "The supported levels are: full, config-only"
    assert err.value.args[0] == expected_msg


def test_validation_replicas_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestDeleteCall(forest="custom-forest", level="full", replicas="X")

    expected_msg = "The supported replicas options are: detach, delete"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    assert ForestDeleteCall(forest="1", level="full").endpoint == "/manage/v2/forests/1"
    assert (
        ForestDeleteCall(forest="custom-forest", level="full").endpoint
        == "/manage/v2/forests/custom-forest"
    )


def test_method(default_forest_delete_call):
    assert default_forest_delete_call.method == "DELETE"


def test_parameters(default_forest_delete_call):
    assert default_forest_delete_call.params == {
        "level": "full",
    }


def test_headers(default_forest_delete_call):
    assert default_forest_delete_call.headers == {}


def test_body(default_forest_delete_call):
    assert default_forest_delete_call.body is None


def test_fully_parametrized_call():
    call = ForestDeleteCall(
        forest="custom-forest",
        level="config-only",
        replicas="delete",
    )
    assert call.method == "DELETE"
    assert call.headers == {}
    assert call.params == {
        "level": "config-only",
        "replicas": "delete",
    }
    assert call.body is None
