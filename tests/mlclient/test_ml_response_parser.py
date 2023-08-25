import xml.etree.ElementTree as ElemTree

import pytest

from mlclient import MLResourcesClient, MLResponseParser


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
def test_default_single_not_parsed_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'


@pytest.mark.ml_access()
def test_default_single_plain_text_str_response(client):
    xqy = "'plain text'"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"


@pytest.mark.ml_access()
def test_default_single_plain_text_int_response(client):
    xqy = "1"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, int)
    assert parsed_resp == 1


@pytest.mark.ml_access()
def test_default_single_plain_text_float_response(client):
    xqy = "1.1"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, float)
    assert parsed_resp == 1.1


@pytest.mark.ml_access()
def test_default_single_plain_text_boolean_response(client):
    xqy = "fn:true()"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, bool)
    assert parsed_resp is True


@pytest.mark.ml_access()
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


@pytest.mark.ml_access()
def test_default_single_json_array_response(client):
    xqy = ('("value", "1", 1, 1.1, fn:true())'
           '=> json:to-array()')
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, list)
    assert parsed_resp == ["value", "1", 1, 1.1, True]


@pytest.mark.ml_access()
def test_default_single_xml_document_node_response(client):
    xqy = "document { element root {} }"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}


@pytest.mark.ml_access()
def test_default_single_xml_element_response(client):
    xqy = "element root {}"
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, ElemTree.Element)
    assert parsed_resp.tag == "root"
    assert parsed_resp.text is None
    assert parsed_resp.attrib == {}


@pytest.mark.ml_access()
def test_default_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), "plain text")'
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)
    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == b'cts:directory-query("/root/", "infinity")'
    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == "plain text"
