import xml.etree.ElementTree as ElemTree
from datetime import date, datetime

import pytest
import responses

from mlclient import MLResourcesClient, MLResponseParser
from tests.tools import MLResponseBuilder


@pytest.fixture(scope="module")
def client():
    return MLResourcesClient(auth_method="digest")


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown(client):
    # Setup
    client.connect()

    yield

    # Teardown
    client.disconnect()


@pytest.mark.ml_access()
def test_default_single_error_response(client):
    xqy = "'missing-quote"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        "XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        "in /eval, at 1:0 [1.0-ml]")


@pytest.mark.ml_access()
@responses.activate
def test_default_single_not_parsed_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'


@pytest.mark.ml_access()
@responses.activate
def test_default_single_empty_response(client):
    xqy = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_empty_response_body()
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []


@pytest.mark.ml_access()
@responses.activate
def test_default_single_plain_text_str_response(client):
    xqy = "'plain text'"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"


@pytest.mark.ml_access()
@responses.activate
def test_default_single_plain_text_int_response(client):
    xqy = "1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, int)
    assert parsed_resp == 1


@pytest.mark.ml_access()
@responses.activate
def test_default_single_plain_text_decimal_response(client):
    xqy = "1.1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part("decimal", "1.1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, float)
    assert parsed_resp == 1.1


@pytest.mark.ml_access()
@responses.activate
def test_default_single_plain_text_boolean_response(client):
    xqy = "fn:true()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part("boolean", "true")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bool)
    assert parsed_resp is True


@pytest.mark.ml_access()
@responses.activate
def test_default_single_plain_text_date_response(client):
    xqy = "fn:current-date()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part("date", "2023-09-14Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, date)
    assert parsed_resp == datetime.strptime("2023-09-14Z", "%Y-%m-%d%z").date()


@pytest.mark.ml_access()
@responses.activate
def test_default_single_plain_text_date_time_response(client):
    xqy = "fn:current-dateTime()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part("dateTime", "2023-09-14T07:30:27.997332Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, datetime)
    assert parsed_resp == datetime.strptime(
        "2023-09-14T07:30:27.997332Z",
        "%Y-%m-%dT%H:%M:%S.%f%z")


@pytest.mark.ml_access()
@responses.activate
def test_default_single_json_map_response(client):
    xqy = ('map:map() '
           '=> map:with("str", "value") '
           '=> map:with("int_str", "1") '
           '=> map:with("int", 1) '
           '=> map:with("float", 1.1) '
           '=> map:with("bool", fn:true())')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}')
    builder.build_post()

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


@pytest.mark.ml_access()
@responses.activate
def test_default_single_json_array_response(client):
    xqy = ('("value", "1", 1, 1.1, fn:true())'
           ' => json:to-array()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part("array", '["value", "1", 1, 1.1, true]')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == ["value", "1", 1, 1.1, True]


@pytest.mark.ml_access()
@responses.activate
def test_default_single_xml_document_node_response(client):
    xqy = "document { element root {} }"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part(
        "document-node()",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<root/>')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}


@pytest.mark.ml_access()
@responses.activate
def test_default_single_xml_element_response(client):
    xqy = "element root {}"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_part("element()", "<root/>")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, ElemTree.Element)
    assert parsed_resp.tag == "root"
    assert parsed_resp.text is None
    assert parsed_resp.attrib == {}


@pytest.mark.ml_access()
def test_default_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == b'cts:directory-query("/root/", "infinity")'
    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == "plain text"


@pytest.mark.ml_access()
def test_default_raw_response(client):
    xqy = ("document { "
           "  element root { "
           "    element child { "
           "      attribute value { 1 } "
           "    } "
           "  }"
           "}")
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, raw=True)
    assert isinstance(parsed_resp, str)
    assert parsed_resp == ('<?xml version="1.0" encoding="UTF-8"?>\n'
                           '<root><child value="1"/></root>')
