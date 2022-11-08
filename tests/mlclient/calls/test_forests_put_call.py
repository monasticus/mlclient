import pytest

from mlclient import exceptions
from mlclient.calls import ForestsPutCall


@pytest.fixture
def default_forests_put_call():
    """Returns a ForestsPutCall instance"""
    body = {
      "operation": "forest-combine",
      "forest": ["forest-1", "forest-2"],
      "forest-name": "forest",
      "host": "custom-host"
    }

    return ForestsPutCall(body=body)


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        ForestsPutCall(body=None)

    assert err.value.args[0] == "No request body provided for PUT /manage/v2/forests!"


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        ForestsPutCall(body=" \n")

    assert err.value.args[0] == "No request body provided for PUT /manage/v2/forests!"


def test_endpoint(default_forests_put_call):
    assert default_forests_put_call.endpoint() == "/manage/v2/forests"
    assert default_forests_put_call.ENDPOINT == "/manage/v2/forests"
    assert ForestsPutCall.ENDPOINT == "/manage/v2/forests"


def test_method(default_forests_put_call):
    assert default_forests_put_call.method() == "PUT"


def test_parameters(default_forests_put_call):
    assert default_forests_put_call.params() == {}


def test_headers_for_dict_body():
    call = ForestsPutCall(body={"server-name": "custom-server"})
    assert call.headers() == {
        "content-type": "application/json"
    }


def test_headers_for_stringified_dict_body():
    call = ForestsPutCall(body='{"server-name": "custom-server"}')
    assert call.headers() == {
        "content-type": "application/json"
    }


def test_headers_for_xml_body():
    body = '<forest-combine xmlns="http://marklogic.com/manage">' \
           '  <forests>' \
           '    <forest>forest-1</forest>' \
           '    <forest>forest-2</forest>' \
           '  </forests>' \
           '  <forest-name>forest</forest-name>' \
           '  <host>custom-host</host>' \
           '</forest-combine>'
    call = ForestsPutCall(body=body)
    assert call.headers() == {
        "content-type": "application/xml"
    }


def test_dict_body():
    body = {
      "operation": "forest-combine",
      "forest": ["forest-1", "forest-2"],
      "forest-name": "forest",
      "host": "custom-host"
    }

    call = ForestsPutCall(body=body)
    assert call.body() == body


def test_stringified_dict_body():
    body = '{"operation": "forest-combine", "forest": ["forest-1", "forest-2"], ' \
           '"forest-name": "forest", "host": "custom-host"}'
    call = ForestsPutCall(body=body)
    assert call.body() == {
      "operation": "forest-combine",
      "forest": ["forest-1", "forest-2"],
      "forest-name": "forest",
      "host": "custom-host"
    }


def test_xml_body():
    body = '<forest-combine xmlns="http://marklogic.com/manage">' \
           '  <forests>' \
           '    <forest>forest-1</forest>' \
           '    <forest>forest-2</forest>' \
           '  </forests>' \
           '  <forest-name>forest</forest-name>' \
           '  <host>custom-host</host>' \
           '</forest-combine>'
    call = ForestsPutCall(body=body)
    assert call.body() == body


def test_fully_parametrized_call():
    body = {
      "operation": "forest-combine",
      "forest": ["forest-1", "forest-2"],
      "forest-name": "forest",
      "host": "custom-host"
    }
    call = ForestsPutCall(body=body)
    assert call.method() == "PUT"
    assert call.headers() == {
        "content-type": "application/json"
    }
    assert call.params() == {}
    assert call.body() == body
