import pytest

from mlclient import exceptions
from mlclient.calls import ServerGetCall


@pytest.fixture()
def default_server_get_call():
    """Returns an ServerGetCall instance"""
    return ServerGetCall(server="App-Services", group_id="Default")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ServerGetCall(server="App-Services", group_id="Default", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ServerGetCall(server="App-Services", group_id="Default", view="X")

    expected_msg = (
        "The supported views are: "
        "describe, default, config, edit, package, "
        "status, xdmp:server-status, properties-schema"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint():
    assert (
        ServerGetCall(server="1", group_id="Default").endpoint == "/manage/v2/servers/1"
    )
    assert (
        ServerGetCall(server="App-Services", group_id="Default").endpoint
        == "/manage/v2/servers/App-Services"
    )


def test_method(default_server_get_call):
    assert default_server_get_call.method == "GET"


def test_parameters(default_server_get_call):
    assert default_server_get_call.params == {
        "group-id": "Default",
        "format": "xml",
        "view": "default",
    }


def test_headers(default_server_get_call):
    assert default_server_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = ServerGetCall(server="App-Services", group_id="Default", data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = ServerGetCall(server="App-Services", group_id="Default", data_format="html")
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = ServerGetCall(server="App-Services", group_id="Default", data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = ServerGetCall(server="App-Services", group_id="Default", data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_server_get_call):
    assert default_server_get_call.body is None


def test_fully_parametrized_call():
    call = ServerGetCall(
        server="App-Services",
        group_id="Default",
        data_format="json",
        view="status",
        host_id="localhost",
        full_refs=False,
        modules=True,
    )
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "group-id": "Default",
        "format": "json",
        "view": "status",
        "host-id": "localhost",
        "fullrefs": "false",
        "modules": "true",
    }
    assert call.body is None
