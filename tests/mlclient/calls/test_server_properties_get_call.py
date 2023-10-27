import pytest

from mlclient import exceptions
from mlclient.calls import ServerPropertiesGetCall


@pytest.fixture()
def default_server_properties_get_call():
    """Returns an ServerPropertiesGetCall instance"""
    return ServerPropertiesGetCall(server="App-Services", group_id="Default")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ServerPropertiesGetCall(
            server="App-Services",
            group_id="Default",
            data_format="text",
        )

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/servers/1/properties"
    expected__name_endpoint = "/manage/v2/servers/App-Services/properties"
    assert (
        ServerPropertiesGetCall(server="1", group_id="Default").endpoint
        == expected__id_endpoint
    )
    assert (
        ServerPropertiesGetCall(server="App-Services", group_id="Default").endpoint
        == expected__name_endpoint
    )


def test_method(default_server_properties_get_call):
    assert default_server_properties_get_call.method == "GET"


def test_parameters(default_server_properties_get_call):
    assert default_server_properties_get_call.params == {
        "group-id": "Default",
        "format": "xml",
    }


def test_headers(default_server_properties_get_call):
    assert default_server_properties_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = ServerPropertiesGetCall(
        server="App-Services",
        group_id="Default",
        data_format=None,
    )
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_html_format():
    call = ServerPropertiesGetCall(
        server="App-Services",
        group_id="Default",
        data_format="html",
    )
    assert call.headers == {
        "Accept": "text/html",
    }


def test_headers_for_xml_format():
    call = ServerPropertiesGetCall(
        server="App-Services",
        group_id="Default",
        data_format="xml",
    )
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = ServerPropertiesGetCall(
        server="App-Services",
        group_id="Default",
        data_format="json",
    )
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_server_properties_get_call):
    assert default_server_properties_get_call.body is None


def test_fully_parametrized_call():
    call = ServerPropertiesGetCall(
        server="App-Services",
        group_id="Default",
        data_format="json",
    )
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "group-id": "Default",
        "format": "json",
    }
    assert call.body is None
