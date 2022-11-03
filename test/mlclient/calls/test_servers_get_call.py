import pytest

from mlclient import exceptions
from mlclient.calls import ServersGetCall


@pytest.fixture
def default_servers_get_call():
    """Returns a ServersGetCall instance"""
    return ServersGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        ServersGetCall(data_format="text")

    assert err.value.args[0] == "The supported formats are: xml, json, html"


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        ServersGetCall(view="X")

    assert err.value.args[0] == "The supported views are: " \
                                "describe, default, status, metrics, package, schema, properties-schema"


def test_endpoint(default_servers_get_call):
    assert default_servers_get_call.endpoint() == "/manage/v2/servers"
    assert default_servers_get_call.ENDPOINT == "/manage/v2/servers"
    assert ServersGetCall.ENDPOINT == "/manage/v2/servers"


def test_method(default_servers_get_call):
    assert default_servers_get_call.method() == "GET"


def test_params(default_servers_get_call):
    assert default_servers_get_call.params() == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_servers_get_call):
    assert default_servers_get_call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_none_format():
    call = ServersGetCall(data_format=None)
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_html_format():
    call = ServersGetCall(data_format="html")
    assert call.headers() == {
        "accept": "text/html"
    }


def test_headers_for_xml_format():
    call = ServersGetCall(data_format="xml")
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_json_format():
    call = ServersGetCall(data_format="json")
    assert call.headers() == {
        "accept": "application/json"
    }


def test_body(default_servers_get_call):
    assert default_servers_get_call.body() is None


def test_fully_parametrized_call():
    call = ServersGetCall(data_format="json",
                          group_id="Default",
                          view="schema",
                          full_refs=True)
    assert call.method() == "GET"
    assert call.headers() == {
        "accept": "application/json"
    }
    assert call.params() == {
        "format": "json",
        "group-id": "Default",
        "view": "schema",
        "fullrefs": "true"
    }
    assert call.body() is None
