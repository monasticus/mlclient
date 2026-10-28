import pytest

from mlclient import exceptions
from mlclient.calls import ApiCall, InitPostCall

LICENSE_DICT = {"license-key": "1234-5678-90AB", "licensee": "Example Licensee"}
LICENSE_JSON = '{"license-key": "1234-5678-90AB", "licensee": "Example Licensee"}'
LICENSE_XML = (
    '<init xmlns="http://marklogic.com/manage">'
    "<license-key>1234-5678-90AB</license-key>"
    "<licensee>Example Licensee</licensee>"
    "</init>"
)


@pytest.fixture
def default_init_post_call():
    """Returns an InitPostCall instance"""
    return InitPostCall()


def test_is_api_call():
    assert issubclass(InitPostCall, ApiCall)


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        InitPostCall(data_format="text")

    expected_msg = "The supported formats are: xml, json"
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        InitPostCall(body=" \n")

    expected_msg = "No request body provided for POST /admin/v1/init!"
    assert err.value.args[0] == expected_msg


def test_validation_json_array_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        InitPostCall(body="[1]")

    expected_msg = "POST /admin/v1/init requires a JSON object or XML body"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_init_post_call):
    assert default_init_post_call.endpoint == "/admin/v1/init"


def test_method(default_init_post_call):
    assert default_init_post_call.method == "POST"


def test_parameters(default_init_post_call):
    assert default_init_post_call.params == {}


def test_headers(default_init_post_call):
    assert default_init_post_call.headers == {
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_headers_for_none_format():
    call = InitPostCall(data_format=None)
    assert call.headers == {
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_headers_for_xml_format():
    call = InitPostCall(data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_headers_for_json_format():
    call = InitPostCall(data_format="json")
    assert call.headers == {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_headers_for_dict_body():
    call = InitPostCall(body=LICENSE_DICT)
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = InitPostCall(body=LICENSE_JSON)
    assert call.headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_xml_body():
    call = InitPostCall(body=LICENSE_XML)
    assert call.headers == {
        "Content-Type": "application/xml",
    }


def test_body(default_init_post_call):
    assert default_init_post_call.body is None


def test_dict_body():
    call = InitPostCall(body=LICENSE_DICT)
    assert call.body == {
        "license-key": "1234-5678-90AB",
        "licensee": "Example Licensee",
    }


def test_stringified_dict_body():
    call = InitPostCall(body=LICENSE_JSON)
    assert call.body == {
        "license-key": "1234-5678-90AB",
        "licensee": "Example Licensee",
    }


def test_xml_body():
    call = InitPostCall(body=LICENSE_XML)
    assert call.body == (
        '<init xmlns="http://marklogic.com/manage">'
        "<license-key>1234-5678-90AB</license-key>"
        "<licensee>Example Licensee</licensee>"
        "</init>"
    )


def test_fully_parametrized_call():
    call = InitPostCall(body=LICENSE_DICT, data_format="json")
    assert call.method == "POST"
    assert call.endpoint == "/admin/v1/init"
    assert call.headers == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    assert call.params == {"format": "json"}
    assert call.body == {
        "license-key": "1234-5678-90AB",
        "licensee": "Example Licensee",
    }
