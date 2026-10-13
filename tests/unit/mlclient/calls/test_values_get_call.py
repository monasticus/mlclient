import pytest

from mlclient import exceptions
from mlclient.calls import ValuesGetCall


def test_empty_options_name_is_preserved():
    call = ValuesGetCall(options="")

    assert call.params == {"format": "xml", "options": ""}


@pytest.fixture
def default_values_get_call():
    """Returns a ValuesGetCall instance"""
    return ValuesGetCall()


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuesGetCall(data_format="text")

    expected_msg = "The supported formats are: json, xml"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_values_get_call):
    assert default_values_get_call.endpoint == "/v1/values"


def test_method(default_values_get_call):
    assert default_values_get_call.method == "GET"


def test_parameters(default_values_get_call):
    assert default_values_get_call.params == {"format": "xml"}


def test_headers(default_values_get_call):
    assert default_values_get_call.headers == {"Accept": "application/xml"}


def test_headers_for_json_format():
    assert ValuesGetCall(data_format="json").headers == {
        "Accept": "application/json",
    }


def test_headers_for_xml_format():
    assert ValuesGetCall(data_format="xml").headers == {
        "Accept": "application/xml",
    }


def test_body(default_values_get_call):
    assert default_values_get_call.body is None


def test_fully_parametrized_call():
    call = ValuesGetCall(
        database="Documents",
        data_format="json",
        options="product-options",
    )
    assert call.method == "GET"
    assert call.endpoint == "/v1/values"
    assert call.headers == {"Accept": "application/json"}
    assert call.params == {
        "database": "Documents",
        "format": "json",
        "options": "product-options",
    }
    assert call.body is None
