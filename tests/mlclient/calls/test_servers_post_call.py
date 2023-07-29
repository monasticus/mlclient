import pytest

from mlclient import exceptions
from mlclient.calls import ServersPostCall


@pytest.fixture
def default_servers_post_call():
    """Returns a ServersPostCall instance"""
    body = {
        "group-name": "Default",
        "server-type": "http",
        "server-name": "custom-server",
        "root": "/",
        "port": 8090,
        "content-database": "Documents",
    }
    return ServersPostCall(body=body)


def test_validation_server_type_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ServersPostCall(server_type="X", body={})

    expected_msg = "The supported server types are: http, odbc, xdbc, webdav"
    assert err.value.args[0] == expected_msg


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ServersPostCall(body=None)

    expected_msg = ("No request body provided for "
                    "POST /manage/v2/servers!")
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ServersPostCall(body=" \n")

    expected_msg = ("No request body provided for "
                    "POST /manage/v2/servers!")
    assert err.value.args[0] == expected_msg


def test_endpoint(default_servers_post_call):
    assert default_servers_post_call.endpoint() == "/manage/v2/servers"
    assert default_servers_post_call.ENDPOINT == "/manage/v2/servers"
    assert ServersPostCall.ENDPOINT == "/manage/v2/servers"


def test_method(default_servers_post_call):
    assert default_servers_post_call.method() == "POST"


def test_parameters(default_servers_post_call):
    assert default_servers_post_call.params() == {}


def test_headers_for_dict_body():
    call = ServersPostCall(body={"server-name": "custom-server"})
    assert call.headers() == {
        "content-type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = ServersPostCall(body='{"server-name": "custom-server"}')
    assert call.headers() == {
        "content-type": "application/json",
    }


def test_headers_for_xml_body():
    body = '<http-server-properties xmlns="http://marklogic.com/manage">' \
           '  <server-name>custom-server</server-name>' \
           '</http-server-properties>'
    call = ServersPostCall(body=body)
    assert call.headers() == {
        "content-type": "application/xml",
    }


def test_dict_body():
    call = ServersPostCall(body={"server-name": "custom-server"})
    assert call.body() == {"server-name": "custom-server"}


def test_stringified_dict_body():
    call = ServersPostCall(body='{"server-name": "custom-server"}')
    assert call.body() == {"server-name": "custom-server"}


def test_xml_body():
    body = '<http-server-properties xmlns="http://marklogic.com/manage">' \
           '  <server-name>custom-server</server-name>' \
           '</http-server-properties>'
    call = ServersPostCall(body=body)
    assert call.body() == body


def test_fully_parametrized_call():
    body = {
        "server-name": "custom-server",
        "root": "/",
        "port": 8090,
        "content-database": "Documents",
    }
    call = ServersPostCall(group_id="Default",
                           server_type="http",
                           body=body)
    assert call.method() == "POST"
    assert call.headers() == {
        "content-type": "application/json",
    }
    assert call.params() == {
        "group-id": "Default",
        "server-type": "http",
    }
    assert call.body() == body
