import pytest

from mlclient import exceptions
from mlclient.calls import DatabaseGetCall


@pytest.fixture
def default_database_get_call():
    """Returns an DatabaseGetCall instance"""
    return DatabaseGetCall(database="Documents")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabaseGetCall(database="Documents", data_format="text")

    assert err.value.args[0] == "The supported formats are: xml, json, html"


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabaseGetCall(database="Documents", view="X")

    assert err.value.args[0] == "The supported views are: " \
                                "describe, default, config, counts, edit, package, " \
                                "status, forest-storage, properties-schema"


def test_endpoint():
    assert DatabaseGetCall(database="1").endpoint() == "/manage/v2/databases/1"
    assert DatabaseGetCall(database="Documents").endpoint() == "/manage/v2/databases/Documents"


def test_method(default_database_get_call):
    assert default_database_get_call.method() == "GET"


def test_parameters(default_database_get_call):
    assert default_database_get_call.params() == {
        "format": "xml",
        "view": "default"
    }


def test_headers(default_database_get_call):
    assert default_database_get_call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_none_format():
    call = DatabaseGetCall(database="Documents", data_format=None)
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_html_format():
    call = DatabaseGetCall(database="Documents", data_format="html")
    assert call.headers() == {
        "accept": "text/html"
    }


def test_headers_for_xml_format():
    call = DatabaseGetCall(database="Documents", data_format="xml")
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_json_format():
    call = DatabaseGetCall(database="Documents", data_format="json")
    assert call.headers() == {
        "accept": "application/json"
    }


def test_body(default_database_get_call):
    assert default_database_get_call.body() is None


def test_fully_parametrized_call():
    call = DatabaseGetCall(database="Documents",
                           data_format="json",
                           view="counts")
    assert call.method() == "GET"
    assert call.headers() == {
        "accept": "application/json"
    }
    assert call.params() == {
        "format": "json",
        "view": "counts"
    }
    assert call.body() is None
