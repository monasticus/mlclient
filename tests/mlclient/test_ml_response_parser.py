import pytest

from mlclient import MLResourceClient, MLResponseParser


@pytest.fixture(scope="module")
def client():
    return MLResourceClient(auth_method="digest")


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown(client):
    # Setup
    client.connect()

    yield

    # Teardown
    client.disconnect()


def test_default_single_not_parsed_response(client):
    xqy = "<root/>"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"<root/>"


def test_default_single_plain_text_not_parsed_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'


def test_default_single_plain_text_str_response(client):
    xqy = "'plain text'"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"


def test_default_single_plain_text_int_response(client):
    xqy = "1"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, int)
    assert parsed_resp == 1


def test_default_single_plain_text_float_response(client):
    xqy = "1.1"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, float)
    assert parsed_resp == 1.1


def test_default_single_plain_text_boolean_response(client):
    xqy = "fn:true()"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, bool)
    assert parsed_resp is True


def test_default_single_json_map_response(client):
    xqy = ('map:map() '
           '=> map:with("str", "value") '
           '=> map:with("int_str", "1") '
           '=> map:with("int", 1) '
           '=> map:with("float", 1.1) '
           '=> map:with("bool", fn:true())')
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {
        "str": "value",
        "int_str": "1",
        "int": 1,
        "float": 1.1,
        "bool": True,
    }


def test_default_single_json_array_response(client):
    xqy = ('("value", "1", 1, 1.1, fn:true())'
           '=> json:to-array()')
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, list)
    assert parsed_resp == ["value", "1", 1, 1.1, True]


def test_default_multiple_responses(client):
    xqy = "(<root/>, 'plain text')"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == b"<root/>"
    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == "plain text"
