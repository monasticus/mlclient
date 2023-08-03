import pytest

from mlclient import exceptions
from mlclient.calls import DatabasePropertiesGetCall


@pytest.fixture()
def default_database_properties_get_call():
    """Returns an DatabasePropertiesGetCall instance"""
    return DatabasePropertiesGetCall(database="Documents")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DatabasePropertiesGetCall(database="Documents", data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/databases/1/properties"
    expected__name_endpoint = "/manage/v2/databases/Documents/properties"
    assert DatabasePropertiesGetCall(
        database="1").endpoint == expected__id_endpoint
    assert DatabasePropertiesGetCall(
        database="Documents").endpoint == expected__name_endpoint


def test_method(default_database_properties_get_call):
    assert default_database_properties_get_call.method == "GET"


def test_parameters(default_database_properties_get_call):
    assert default_database_properties_get_call.params == {
        "format": "xml",
    }


def test_headers(default_database_properties_get_call):
    assert default_database_properties_get_call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_none_format():
    call = DatabasePropertiesGetCall(database="Documents", data_format=None)
    assert call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_html_format():
    call = DatabasePropertiesGetCall(database="Documents", data_format="html")
    assert call.headers == {
        "accept": "text/html",
    }


def test_headers_for_xml_format():
    call = DatabasePropertiesGetCall(database="Documents", data_format="xml")
    assert call.headers == {
        "accept": "application/xml",
    }


def test_headers_for_json_format():
    call = DatabasePropertiesGetCall(database="Documents", data_format="json")
    assert call.headers == {
        "accept": "application/json",
    }


def test_body(default_database_properties_get_call):
    assert default_database_properties_get_call.body is None


def test_fully_parametrized_call():
    call = DatabasePropertiesGetCall(database="Documents",
                                     data_format="json")
    assert call.method == "GET"
    assert call.headers == {
        "accept": "application/json",
    }
    assert call.params == {
        "format": "json",
    }
    assert call.body is None
