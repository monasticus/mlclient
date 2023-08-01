import pytest

from mlclient import exceptions
from mlclient.calls import ForestsPostCall


@pytest.fixture()
def default_forests_post_call():
    """Returns a ForestsPostCall instance"""
    body = {
      "forest-name": "custom-forest",
      "host": "custom-host",
      "database": "custom-database",
    }
    return ForestsPostCall(body=body)


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestsPostCall(body=None)

    expected_msg = ("No request body provided for "
                    "POST /manage/v2/forests!")
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestsPostCall(body=" \n")

    expected_msg = ("No request body provided for "
                    "POST /manage/v2/forests!")
    assert err.value.args[0] == expected_msg


def test_endpoint(default_forests_post_call):
    assert default_forests_post_call.endpoint() == "/manage/v2/forests"
    assert default_forests_post_call.ENDPOINT == "/manage/v2/forests"
    assert ForestsPostCall.ENDPOINT == "/manage/v2/forests"


def test_method(default_forests_post_call):
    assert default_forests_post_call.method() == "POST"


def test_parameters(default_forests_post_call):
    assert default_forests_post_call.params() == {}


def test_headers_for_dict_body():
    call = ForestsPostCall(body={"server-name": "custom-server"})
    assert call.headers() == {
        "content-type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = ForestsPostCall(body='{"server-name": "custom-server"}')
    assert call.headers() == {
        "content-type": "application/json",
    }


def test_headers_for_xml_body():
    body = ('<forest-create xmlns="http://marklogic.com/manage">'
            '  <forest-name>custom-forest</forest-name>'
            '  <host>custom-host</host>'
            '</forest-create>')
    call = ForestsPostCall(body=body)
    assert call.headers() == {
        "content-type": "application/xml",
    }


def test_dict_body():
    body = {
      "forest-name": "custom-forest",
      "host": "custom-host",
    }

    call = ForestsPostCall(body=body)
    assert call.body() == body


def test_stringified_dict_body():
    call = ForestsPostCall(
        body='{"forest-name": "custom-forest", "host": "custom-host"}')
    assert call.body() == {
        "forest-name": "custom-forest",
        "host": "custom-host",
    }


def test_xml_body():
    body = ('<forest-create xmlns="http://marklogic.com/manage">'
            '  <forest-name>custom-forest</forest-name>'
            '  <host>custom-host</host>'
            '</forest-create>')
    call = ForestsPostCall(body=body)
    assert call.body() == body


def test_fully_parametrized_call():
    body = {
      "forest-name": "custom-forest",
      "host": "custom-host",
      "database": "custom-database",
    }
    call = ForestsPostCall(
        body=body,
        wait_for_forest_to_mount=False)
    assert call.method() == "POST"
    assert call.headers() == {
        "content-type": "application/json",
    }
    assert call.params() == {
        "wait-for-forest-to-mount": "false",
    }
    assert call.body() == body
