import pytest

from mlclient import exceptions
from mlclient.calls import ForestPostCall


@pytest.fixture
def default_forest_post_call():
    """Returns an ForestPostCall instance"""
    return ForestPostCall(forest="custom-forest", body={"state": "clear"})


def test_validation_no_state_param_in_body():
    with pytest.raises(exceptions.WrongParameters) as err:
        ForestPostCall(forest="custom-forest", body={})

    assert err.value.args[0] == "You must include the 'state' parameter within a body!"


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        ForestPostCall(forest="custom-forest", body={"state": "XXX"})

    assert err.value.args[0] == "The supported states are: clear, merge, restart, attach, detach, retire, employ"


def test_endpoint():
    assert ForestPostCall(forest="1",
                          body={"state": "clear"}).endpoint() == "/manage/v2/forests/1"
    assert ForestPostCall(forest="custom-forest",
                          body={"state": "clear"}).endpoint() == "/manage/v2/forests/custom-forest"


def test_method(default_forest_post_call):
    assert default_forest_post_call.method() == "POST"


def test_parameters(default_forest_post_call):
    assert default_forest_post_call.params() == {}


def test_headers(default_forest_post_call):
    assert default_forest_post_call.headers() == {
        "content-type": "application/x-www-form-urlencoded"
    }


def test_body(default_forest_post_call):
    assert default_forest_post_call.body() == {"state": "clear"}
