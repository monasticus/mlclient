import pytest

from mlclient import exceptions
from mlclient.calls import DatabasesPostCall


@pytest.fixture
def default_databases_post_call():
    """Returns an DatabasesPostCall instance"""
    return DatabasesPostCall(body={"database-name": "custom-db"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasesPostCall()

    assert err.value.args[0] == "No request body provided for POST /manage/v2/databases!"


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabasesPostCall(body=" \n")

    assert err.value.args[0] == "No request body provided for POST /manage/v2/databases!"


def test_endpoint(default_databases_post_call):
    assert default_databases_post_call.endpoint() == "/manage/v2/databases"
    assert default_databases_post_call.ENDPOINT == "/manage/v2/databases"
    assert DatabasesPostCall.ENDPOINT == "/manage/v2/databases"


def test_method(default_databases_post_call):
    assert default_databases_post_call.method() == "POST"


def test_headers_for_dict_body():
    call = DatabasesPostCall(body={"database-name": "custom-db"})
    assert {
        "content-type": "application/json"
    } == call.headers()


def test_headers_for_stringified_dict_body():
    call = DatabasesPostCall(body='{"database-name": "custom-db"}')
    assert {
        "content-type": "application/json"
    } == call.headers()


def test_headers_for_xml_body():
    body = '<database-properties xmlns="http://marklogic.com/manage">' \
           '  <database-name>custom-db</database-name>' \
           '</database-properties>'
    call = DatabasesPostCall(body=body)
    assert {
        "content-type": "application/xml"
    } == call.headers()


def test_dict_body():
    call = DatabasesPostCall(body={"database-name": "custom-db"})
    assert call.body() == {"database-name": "custom-db"}


def test_stringified_dict_body():
    call = DatabasesPostCall(body='{"database-name": "custom-db"}')
    assert call.body() == {"database-name": "custom-db"}


def test_xml_body():
    body = '<database-properties xmlns="http://marklogic.com/manage">' \
           '  <database-name>custom-db</database-name>' \
           '</database-properties>'
    call = DatabasesPostCall(body=body)
    assert call.body() == body


def test_fully_parametrized_call():
    call = DatabasesPostCall(body={"database-name": "custom-db"})
    assert call.method() == "POST"
    assert {
        "content-type": "application/json"
    } == call.headers()
    assert {} == call.params()
    assert call.body() == {"database-name": "custom-db"}
