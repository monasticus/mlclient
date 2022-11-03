import pytest

from mlclient import exceptions
from mlclient.calls import DatabasePropertiesGetCall


@pytest.fixture
def default_database_properties_get_call():
    """Returns an DatabasePropertiesGetCall instance"""
    return DatabasePropertiesGetCall(database_name="Documents")


def test_validation_no_database_id_nor_database_name():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePropertiesGetCall()

    assert err.value.args[0] == "You must include either the database_id or the database_name parameter!"


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePropertiesGetCall(database_name="Documents", data_format="text")

    assert err.value.args[0] == "The supported formats are: xml, json, html"


def test_endpoint():
    expected__id_endpoint = "/manage/v2/databases/1/properties"
    expected__name_endpoint = "/manage/v2/databases/Documents/properties"
    assert DatabasePropertiesGetCall(database_id="1").endpoint() == expected__id_endpoint
    assert DatabasePropertiesGetCall(database_name="Documents").endpoint() == expected__name_endpoint
    assert DatabasePropertiesGetCall(database_id="1", database_name="Documents").endpoint() == expected__id_endpoint


def test_method(default_database_properties_get_call):
    assert default_database_properties_get_call.method() == "GET"


def test_headers_for_default_format():
    call = DatabasePropertiesGetCall(database_name="Documents")
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_none_format():
    call = DatabasePropertiesGetCall(database_name="Documents", data_format=None)
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_html_format():
    call = DatabasePropertiesGetCall(database_name="Documents", data_format="html")
    assert {
        "accept": "text/html"
    } == call.headers()


def test_headers_for_xml_format():
    call = DatabasePropertiesGetCall(database_name="Documents", data_format="xml")
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_json_format():
    call = DatabasePropertiesGetCall(database_name="Documents", data_format="json")
    assert {
        "accept": "application/json"
    } == call.headers()


def test_body(default_database_properties_get_call):
    assert not default_database_properties_get_call.body()


def test_fully_parametrized_call():
    call = DatabasePropertiesGetCall(database_name="Documents",
                                     data_format="json")
    assert call.method() == "GET"
    assert {
        "accept": "application/json"
    } == call.headers()
    assert {
         "format": "json"
    } == call.params()
    assert call.body() is None
