import pytest

from mlclient import exceptions
from mlclient.calls import ServerPropertiesPutCall


@pytest.fixture()
def default_server_properties_put_call():
    """Returns an ServerPropertiesPutCall instance"""
    return ServerPropertiesPutCall(
        server="App-Services",
        group_id="Default",
        body={"port": 8343},
    )


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ServerPropertiesPutCall(server="App-Services", group_id="Default", body=None)

    expected_msg = (
        "No request body provided for PUT /manage/v2/servers/{id|name}/properties!"
    )
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ServerPropertiesPutCall(server="App-Services", group_id="Default", body=" \n")

    expected_msg = (
        "No request body provided for PUT /manage/v2/servers/{id|name}/properties!"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/servers/1/properties"
    expected__name_endpoint = "/manage/v2/servers/App-Services/properties"
    assert (
        ServerPropertiesPutCall(
            server="1",
            group_id="Default",
            body={"port": 8343},
        ).endpoint
        == expected__id_endpoint
    )
    assert (
        ServerPropertiesPutCall(
            server="App-Services",
            group_id="Default",
            body={"port": 8343},
        ).endpoint
        == expected__name_endpoint
    )


def test_method(default_server_properties_put_call):
    assert default_server_properties_put_call.method == "PUT"


def test_parameters(default_server_properties_put_call):
    assert default_server_properties_put_call.params == {
        "group-id": "Default",
    }


def test_headers_for_dict_body():
    call = ServerPropertiesPutCall(
        server="App-Services",
        group_id="Default",
        body={"port": 8343},
    )
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = ServerPropertiesPutCall(
        server="App-Services",
        group_id="Default",
        body='{"port": 8343}',
    )
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_xml_body():
    body = (
        '<http-server-properties xmlns="http://marklogic.com/manage">'
        "  <port>8343</port>"
        "</http-server-properties>"
    )
    call = ServerPropertiesPutCall(server="App-Services", group_id="Default", body=body)
    assert call.headers == {
        "Content-Type": "application/xml",
    }


def test_dict_body():
    call = ServerPropertiesPutCall(
        server="App-Services",
        group_id="Default",
        body={"port": 8343},
    )
    assert call.body == {"port": 8343}


def test_stringified_dict_body():
    call = ServerPropertiesPutCall(
        server="App-Services",
        group_id="Default",
        body='{"port": 8343}',
    )
    assert call.body == {"port": 8343}


def test_xml_body():
    body = (
        '<http-server-properties xmlns="http://marklogic.com/manage">'
        "  <port>8343</port>"
        "</http-server-properties>"
    )
    call = ServerPropertiesPutCall(server="App-Services", group_id="Default", body=body)
    assert call.body == body
