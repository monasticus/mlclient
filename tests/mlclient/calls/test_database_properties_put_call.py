import pytest

from mlclient import exceptions
from mlclient.calls import DatabasePropertiesPutCall


@pytest.fixture
def default_database_properties_put_call():
    """Returns an DatabasePropertiesPutCall instance"""
    return DatabasePropertiesPutCall(database="Documents", body={"database-name": "custom-db"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePropertiesPutCall(database="Documents", body=None)

    assert err.value.args[0] == "No request body provided for PUT /manage/v2/databases/{id|name}/properties!"


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePropertiesPutCall(database="Documents", body=" \n")

    assert err.value.args[0] == "No request body provided for PUT /manage/v2/databases/{id|name}/properties!"


def test_endpoint():
    expected__id_endpoint = "/manage/v2/databases/1/properties"
    expected__name_endpoint = "/manage/v2/databases/Documents/properties"
    assert DatabasePropertiesPutCall(database="1",
                                     body={"database-name": "custom-db"}).endpoint() == expected__id_endpoint
    assert DatabasePropertiesPutCall(database="Documents",
                                     body={"database-name": "custom-db"}).endpoint() == expected__name_endpoint


def test_method(default_database_properties_put_call):
    assert default_database_properties_put_call.method() == "PUT"


def test_parameters(default_database_properties_put_call):
    assert default_database_properties_put_call.params() == {}


def test_headers_for_dict_body():
    call = DatabasePropertiesPutCall(database="Documents", body={"database-name": "custom-db"})
    assert call.headers() == {
        "content-type": "application/json"
    }


def test_headers_for_stringified_dict_body():
    call = DatabasePropertiesPutCall(database="Documents", body='{"database-name": "custom-db"}')
    assert call.headers() == {
        "content-type": "application/json"
    }


def test_headers_for_xml_body():
    body = '<database-properties xmlns="http://marklogic.com/manage">' \
           '  <database-name>custom-db</database-name>' \
           '</database-properties>'
    call = DatabasePropertiesPutCall(database="Documents", body=body)
    assert call.headers() == {
        "content-type": "application/xml"
    }


def test_dict_body():
    call = DatabasePropertiesPutCall(database="Documents", body={"database-name": "custom-db"})
    assert call.body() == {"database-name": "custom-db"}


def test_stringified_dict_body():
    call = DatabasePropertiesPutCall(database="Documents", body='{"database-name": "custom-db"}')
    assert call.body() == {"database-name": "custom-db"}


def test_xml_body():
    body = '<database-properties xmlns="http://marklogic.com/manage">' \
           '  <database-name>custom-db</database-name>' \
           '</database-properties>'
    call = DatabasePropertiesPutCall(database="Documents", body=body)
    assert call.body() == body
