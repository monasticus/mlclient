import pytest

from mlclient import exceptions
from mlclient.calls import DatabasePostCall


@pytest.fixture
def default_database_post_call():
    """Returns an DatabasePostCall instance"""
    return DatabasePostCall(database="Documents", body={"operation": "clear-database"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePostCall(database="Documents", body=None)

    assert err.value.args[0] == "No request body provided for POST /manage/v2/databases/{id|name}!"


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePostCall(database="Documents", body=" \n")

    assert err.value.args[0] == "No request body provided for POST /manage/v2/databases/{id|name}!"


def test_endpoint():
    assert DatabasePostCall(database="1",
                            body={"operation": "clear-database"}).endpoint() == "/manage/v2/databases/1"
    assert DatabasePostCall(database="Documents",
                            body={"operation": "clear-database"}).endpoint() == "/manage/v2/databases/Documents"


def test_method(default_database_post_call):
    assert default_database_post_call.method() == "POST"


def test_parameters(default_database_post_call):
    assert default_database_post_call.params() == {}


def test_headers_for_dict_body():
    call = DatabasePostCall(database="Documents", body={"operation": "clear-database"})
    assert call.headers() == {
        "content-type": "application/json"
    }


def test_headers_for_stringified_dict_body():
    call = DatabasePostCall(database="Documents", body='{"operation": "clear-database"}')
    assert call.headers() == {
        "content-type": "application/json"
    }


def test_headers_for_xml_body():
    body = '<clear-database-operation xmlns="http://marklogic.com/manage">' \
           '    <operation>clear-database</operation>' \
           '</clear-database-operation>'
    call = DatabasePostCall(database="Documents", body=body)
    assert call.headers() == {
        "content-type": "application/xml"
    }


def test_dict_body():
    call = DatabasePostCall(database="Documents", body={"operation": "clear-database"})
    assert call.body() == {"operation": "clear-database"}


def test_stringified_dict_body():
    call = DatabasePostCall(database="Documents", body='{"operation": "clear-database"}')
    assert call.body() == {"operation": "clear-database"}


def test_xml_body():
    body = '<clear-database-operation xmlns="http://marklogic.com/manage">' \
           '    <operation>clear-database</operation>' \
           '</clear-database-operation>'
    call = DatabasePostCall(database="Documents", body=body)
    assert call.body() == body
