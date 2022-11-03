import pytest

from mlclient import exceptions
from mlclient.calls import DatabasePostCall


@pytest.fixture
def default_database_post_call():
    """Returns an DatabasePostCall instance"""
    return DatabasePostCall(database_name="Documents", body={"operation": "clear-database"})


def test_validation_no_database_id_nor_database_name():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePostCall()

    assert err.value.args[0] == "You must include either the database_id or the database_name parameter!"


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePostCall(database_name="Documents")

    assert err.value.args[0] == "No request body provided for POST /manage/v2/databases/Documents!"


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasePostCall(database_name="Documents", body=" \n")

    assert err.value.args[0] == "No request body provided for POST /manage/v2/databases/Documents!"


def test_endpoint():
    assert DatabasePostCall(database_id="1",
                            body={"operation": "clear-database"}).endpoint() == "/manage/v2/databases/1"
    assert DatabasePostCall(database_name="Documents",
                            body={"operation": "clear-database"}).endpoint() == "/manage/v2/databases/Documents"
    assert DatabasePostCall(database_id="1",
                            database_name="Documents",
                            body={"operation": "clear-database"}).endpoint() == "/manage/v2/databases/1"


def test_method(default_database_post_call):
    assert default_database_post_call.method() == "POST"


def test_parameters(default_database_post_call):
    assert default_database_post_call.params() == {}


def test_headers_for_dict_body():
    call = DatabasePostCall(database_name="Documents", body={"operation": "clear-database"})
    assert call.headers() == {
        "content-type": "application/json"
    }


def test_headers_for_stringified_dict_body():
    call = DatabasePostCall(database_name="Documents", body='{"operation": "clear-database"}')
    assert call.headers() == {
        "content-type": "application/json"
    }


def test_headers_for_xml_body():
    body = '<clear-database-operation xmlns="http://marklogic.com/manage">' \
           '    <operation>clear-database</operation>' \
           '</clear-database-operation>'
    call = DatabasePostCall(database_name="Documents", body=body)
    assert call.headers() == {
        "content-type": "application/xml"
    }


def test_dict_body():
    call = DatabasePostCall(database_name="Documents", body={"operation": "clear-database"})
    assert call.body() == {"operation": "clear-database"}


def test_stringified_dict_body():
    call = DatabasePostCall(database_name="Documents", body='{"operation": "clear-database"}')
    assert call.body() == {"operation": "clear-database"}


def test_xml_body():
    body = '<clear-database-operation xmlns="http://marklogic.com/manage">' \
           '    <operation>clear-database</operation>' \
           '</clear-database-operation>'
    call = DatabasePostCall(database_name="Documents", body=body)
    assert call.body() == body
