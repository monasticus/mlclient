import pytest

from mlclient import exceptions
from mlclient.calls import DatabaseGetCall


@pytest.fixture
def default_database_get_call():
    """Returns an DatabaseGetCall instance"""
    return DatabaseGetCall(database_name="Documents")


def test_validation_no_database_id_nor_database_name():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabaseGetCall()

    assert err.value.args[0] == "You must include either the database_id or the database_name parameter!"


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabaseGetCall(database_name="Documents", data_format="text")

    assert err.value.args[0] == "The supported formats are: xml, json, html"


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabaseGetCall(database_name="Documents", view="X")

    assert err.value.args[0] == "The supported views are: " \
                                "describe, default, config, counts, edit, package, " \
                                "status, forest-storage, properties-schema"


def test_endpoint():
    assert DatabaseGetCall(database_id="1").endpoint() == "/manage/v2/databases/1"
    assert DatabaseGetCall(database_name="Documents").endpoint() == "/manage/v2/databases/Documents"
    assert DatabaseGetCall(database_id="1", database_name="Documents").endpoint() == "/manage/v2/databases/1"


def test_method(default_database_get_call):
    assert default_database_get_call.method() == "GET"


def test_headers_for_default_format():
    call = DatabaseGetCall(database_name="Documents")
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_none_format():
    call = DatabaseGetCall(database_name="Documents", data_format=None)
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_html_format():
    call = DatabaseGetCall(database_name="Documents", data_format="html")
    assert {
        "accept": "text/html"
    } == call.headers()


def test_headers_for_xml_format():
    call = DatabaseGetCall(database_name="Documents", data_format="xml")
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_json_format():
    call = DatabaseGetCall(database_name="Documents", data_format="json")
    assert {
        "accept": "application/json"
    } == call.headers()


def test_body(default_database_get_call):
    assert default_database_get_call.body() is None


def test_fully_parametrized_call():
    call = DatabaseGetCall(database_name="Documents",
                           data_format="json",
                           view="counts")
    assert call.method() == "GET"
    assert {
        "accept": "application/json"
    } == call.headers()
    assert {
         "format": "json",
         "view": "counts"
    } == call.params()
    assert call.body() is None
