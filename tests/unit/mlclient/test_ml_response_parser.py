import xml.etree.ElementTree as ElemTree
import zlib
from datetime import date, datetime
from pathlib import Path

import pytest
import responses

from mlclient import MLResourcesClient, MLResponseParser
from mlclient.calls.model import DocumentsBodyPart
from tests import tools
from tests.tools import MLResponseBuilder


@pytest.fixture(scope="module")
def client():
    return MLResourcesClient()


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown(client):
    # Setup
    client.connect()

    yield

    # Teardown
    client.disconnect()


@responses.activate
def test_parse_error_response_html(client):
    xqy = "'missing-quote"

    response_body_path = tools.get_test_resource_path(__file__, "error-response.html")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_content_type("text/html; charset=utf-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        "XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        "in /eval, at 1:0 [1.0-ml]"
    )


@responses.activate
def test_parse_text_error_response_html(client):
    xqy = "'missing-quote"

    response_body_path = tools.get_test_resource_path(__file__, "error-response.html")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_content_type("text/html; charset=utf-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        "XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        "in /eval, at 1:0 [1.0-ml]"
    )


@responses.activate
def test_parse_bytes_error_response_html(client):
    xqy = "'missing-quote"

    response_body_path = tools.get_test_resource_path(__file__, "error-response.html")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_content_type("text/html; charset=utf-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == (
        b"XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        b"in /eval, at 1:0 [1.0-ml]"
    )


@responses.activate
def test_parse_with_headers_error_response_html(client):
    xqy = "'missing-quote"

    response_body_path = tools.get_test_resource_path(__file__, "error-response.html")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_content_type("text/html; charset=utf-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        "XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        "in /eval, at 1:0 [1.0-ml]"
    )
    assert headers == {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": "1014",
    }


@responses.activate
def test_parse_text_with_headers_error_response_html(client):
    xqy = "'missing-quote"

    response_body_path = tools.get_test_resource_path(__file__, "error-response.html")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_content_type("text/html; charset=utf-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        "XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        "in /eval, at 1:0 [1.0-ml]"
    )
    assert headers == {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": "1014",
    }


@responses.activate
def test_parse_bytes_with_headers_error_response_html(client):
    xqy = "'missing-quote"

    response_body_path = tools.get_test_resource_path(__file__, "error-response.html")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_content_type("text/html; charset=utf-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == (
        b"XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        b"in /eval, at 1:0 [1.0-ml]"
    )
    assert headers == {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": "1014",
    }


@responses.activate
def test_parse_error_response_xml(client):
    response_body_path = tools.get_test_resource_path(__file__, "error-response.xml")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("database", "Document")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    resp = client.delete_documents(uri="/some/dir/doc1.xml", database="Document")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "XDMP-NOSUCHDB",
            "message": "XDMP-NOSUCHDB: No such database Document",
        },
    }


@responses.activate
def test_parse_text_error_response_xml(client):
    response_body_path = tools.get_test_resource_path(__file__, "error-response.xml")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("database", "Document")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    resp = client.delete_documents(uri="/some/dir/doc1.xml", database="Document")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        '{"errorResponse": {'
        '"statusCode": 404, '
        '"status": "Not Found", '
        '"messageCode": "XDMP-NOSUCHDB", '
        '"message": "XDMP-NOSUCHDB: No such database Document"'
        "}}"
    )


@responses.activate
def test_parse_bytes_error_response_xml(client):
    response_body_path = tools.get_test_resource_path(__file__, "error-response.xml")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("database", "Document")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    resp = client.delete_documents(uri="/some/dir/doc1.xml", database="Document")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == (
        b'{"errorResponse": {'
        b'"statusCode": 404, '
        b'"status": "Not Found", '
        b'"messageCode": "XDMP-NOSUCHDB", '
        b'"message": "XDMP-NOSUCHDB: No such database Document"'
        b"}}"
    )


@responses.activate
def test_parse_with_headers_error_response_xml(client):
    response_body_path = tools.get_test_resource_path(__file__, "error-response.xml")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("database", "Document")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    resp = client.delete_documents(uri="/some/dir/doc1.xml", database="Document")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "XDMP-NOSUCHDB",
            "message": "XDMP-NOSUCHDB: No such database Document",
        },
    }
    assert headers == {
        "Content-Type": "application/xml; charset=UTF-8",
        "Content-Length": "226",
    }


@responses.activate
def test_parse_text_with_headers_error_response_xml(client):
    response_body_path = tools.get_test_resource_path(__file__, "error-response.xml")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("database", "Document")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    resp = client.delete_documents(uri="/some/dir/doc1.xml", database="Document")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        '{"errorResponse": {'
        '"statusCode": 404, '
        '"status": "Not Found", '
        '"messageCode": "XDMP-NOSUCHDB", '
        '"message": "XDMP-NOSUCHDB: No such database Document"'
        "}}"
    )
    assert headers == {
        "Content-Type": "application/xml; charset=UTF-8",
        "Content-Length": "226",
    }


@responses.activate
def test_parse_bytes_with_headers_error_response_xml(client):
    response_body_path = tools.get_test_resource_path(__file__, "error-response.xml")
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("database", "Document")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    resp = client.delete_documents(uri="/some/dir/doc1.xml", database="Document")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == (
        b'{"errorResponse": {'
        b'"statusCode": 404, '
        b'"status": "Not Found", '
        b'"messageCode": "XDMP-NOSUCHDB", '
        b'"message": "XDMP-NOSUCHDB: No such database Document"'
        b"}}"
    )
    assert headers == {
        "Content-Type": "application/xml; charset=UTF-8",
        "Content-Length": "226",
    }


@responses.activate
def test_parse_error_response_json(client):
    uri = "/some/dir/doc.xml"
    error = {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "RESTAPI-NODOCUMENT",
            "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
            "Resource or document does not exist:  "
            "category: content message: /some/dir/doc.xml",
        },
    }

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(error)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == error


@responses.activate
def test_parse_text_error_response_json(client):
    uri = "/some/dir/doc.xml"
    error = {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "RESTAPI-NODOCUMENT",
            "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
            "Resource or document does not exist:  "
            "category: content message: /some/dir/doc.xml",
        },
    }

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(error)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        '{"errorResponse": {'
        '"statusCode": 404, '
        '"status": "Not Found", '
        '"messageCode": "RESTAPI-NODOCUMENT", '
        '"message": "RESTAPI-NODOCUMENT: (err:FOER0000) '
        f'Resource or document does not exist:  category: content message: {uri}"'
        "}}"
    )


@responses.activate
def test_parse_bytes_error_response_json(client):
    uri = "/some/dir/doc.xml"
    error = {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "RESTAPI-NODOCUMENT",
            "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
            "Resource or document does not exist:  "
            "category: content message: /some/dir/doc.xml",
        },
    }

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(error)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == (
        b'{"errorResponse": {'
        b'"statusCode": 404, '
        b'"status": "Not Found", '
        b'"messageCode": "RESTAPI-NODOCUMENT", '
        b'"message": "RESTAPI-NODOCUMENT: (err:FOER0000) '
        + "Resource or document does not exist:  "
        f'category: content message: {uri}"'.encode()
        + b"}}"
    )


@responses.activate
def test_parse_with_headers_error_response_json(client):
    uri = "/some/dir/doc.xml"
    error = {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "RESTAPI-NODOCUMENT",
            "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
            "Resource or document does not exist:  "
            "category: content message: /some/dir/doc.xml",
        },
    }

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(error)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == error
    assert headers == {
        "Content-Type": "application/json; charset=UTF-8",
        "Content-Length": "230",
    }


@responses.activate
def test_parse_text_with_headers_error_response_json(client):
    uri = "/some/dir/doc.xml"
    error = {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "RESTAPI-NODOCUMENT",
            "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
            "Resource or document does not exist:  "
            "category: content message: /some/dir/doc.xml",
        },
    }

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(error)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        "{"
        '"errorResponse": '
        "{"
        '"statusCode": 404, '
        '"status": "Not Found", '
        '"messageCode": "RESTAPI-NODOCUMENT", '
        '"message": "RESTAPI-NODOCUMENT: (err:FOER0000) '
        "Resource or document does not exist: "
        ' category: content message: /some/dir/doc.xml"'
        "}"
        "}"
    )
    assert headers == {
        "Content-Type": "application/json; charset=UTF-8",
        "Content-Length": "230",
    }


@responses.activate
def test_parse_bytes_with_headers_error_response_json(client):
    uri = "/some/dir/doc.xml"
    error = {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "RESTAPI-NODOCUMENT",
            "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
            "Resource or document does not exist:  "
            "category: content message: /some/dir/doc.xml",
        },
    }

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(error)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == (
        b"{"
        b'"errorResponse": '
        b"{"
        b'"statusCode": 404, '
        b'"status": "Not Found", '
        b'"messageCode": "RESTAPI-NODOCUMENT", '
        b'"message": "RESTAPI-NODOCUMENT: (err:FOER0000) '
        b"Resource or document does not exist: "
        b' category: content message: /some/dir/doc.xml"'
        b"}"
        b"}"
    )
    assert headers == {
        "Content-Type": "application/json; charset=UTF-8",
        "Content-Length": "230",
    }


@responses.activate
def test_parse_non_multipart_mixed_response_xml(client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/xml; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_body('<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}


@responses.activate
def test_parse_text_non_multipart_mixed_response_xml(client):
    uri = "/some/dir/doc1.xml"
    content = '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/xml; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == content


@responses.activate
def test_parse_bytes_non_multipart_mixed_response_xml(client):
    uri = "/some/dir/doc1.xml"
    content = '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/xml; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content.encode("utf-8")


@responses.activate
def test_parse_with_headers_non_multipart_mixed_response_xml(client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/xml; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_body('<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}
    assert headers == {
        "vnd.marklogic.document-format": "xml",
        "Content-Type": "application/xml; charset=utf-8",
        "Content-Length": "46",
    }


@responses.activate
def test_parse_text_with_headers_non_multipart_mixed_response_xml(client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/xml; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_body('<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert headers == {
        "vnd.marklogic.document-format": "xml",
        "Content-Type": "application/xml; charset=utf-8",
        "Content-Length": "46",
    }


@responses.activate
def test_parse_bytes_with_headers_non_multipart_mixed_response_xml(client):
    uri = "/some/dir/doc1.xml"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/xml; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "xml")
    builder.with_response_status(200)
    builder.with_response_body('<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert headers == {
        "vnd.marklogic.document-format": "xml",
        "Content-Type": "application/xml; charset=utf-8",
        "Content-Length": "46",
    }


@responses.activate
def test_parse_non_multipart_mixed_response_json(client):
    uri = "/some/dir/doc2.json"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body('{"root":{"child":"data2"}}')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {"root": {"child": "data2"}}


@responses.activate
def test_parse_text_non_multipart_mixed_response_json(client):
    uri = "/some/dir/doc2.json"
    content = '{"root":{"child":"data2"}}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == content


@responses.activate
def test_parse_bytes_non_multipart_mixed_response_json(client):
    uri = "/some/dir/doc2.json"
    content = '{"root":{"child":"data2"}}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content.encode("utf-8")


@responses.activate
def test_parse_with_headers_non_multipart_mixed_response_json(client):
    uri = "/some/dir/doc2.json"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body('{"root":{"child":"data2"}}')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {"root": {"child": "data2"}}
    assert headers == {
        "vnd.marklogic.document-format": "json",
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": "26",
    }


@responses.activate
def test_parse_text_with_headers_non_multipart_mixed_response_json(client):
    uri = "/some/dir/doc2.json"
    content = '{"root":{"child":"data2"}}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == content
    assert headers == {
        "vnd.marklogic.document-format": "json",
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": "26",
    }


@responses.activate
def test_parse_bytes_with_headers_non_multipart_mixed_response_json(client):
    uri = "/some/dir/doc2.json"
    content = '{"root":{"child":"data2"}}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "json")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content.encode("utf-8")
    assert headers == {
        "vnd.marklogic.document-format": "json",
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": "26",
    }


@responses.activate
def test_parse_non_multipart_mixed_response_text(client):
    uri = "/some/dir/doc3.xqy"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "text")
    builder.with_response_status(200)
    builder.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'xquery version "1.0-ml";\n\nfn:current-date()'


@responses.activate
def test_parse_text_non_multipart_mixed_response_text(client):
    uri = "/some/dir/doc3.xqy"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "text")
    builder.with_response_status(200)
    builder.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'xquery version "1.0-ml";\n\nfn:current-date()'


@responses.activate
def test_parse_bytes_non_multipart_mixed_response_text(client):
    uri = "/some/dir/doc3.xqy"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "text")
    builder.with_response_status(200)
    builder.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'xquery version "1.0-ml";\n\nfn:current-date()'


@responses.activate
def test_parse_with_headers_non_multipart_mixed_response_text(client):
    uri = "/some/dir/doc3.xqy"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "text")
    builder.with_response_status(200)
    builder.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers == {
        "vnd.marklogic.document-format": "text",
        "Content-Type": "application/vnd.marklogic-xdmp; charset=utf-8",
        "Content-Length": "43",
    }


@responses.activate
def test_parse_text_with_headers_non_multipart_mixed_response_text(client):
    uri = "/some/dir/doc3.xqy"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "text")
    builder.with_response_status(200)
    builder.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers == {
        "vnd.marklogic.document-format": "text",
        "Content-Type": "application/vnd.marklogic-xdmp; charset=utf-8",
        "Content-Length": "43",
    }


@responses.activate
def test_parse_bytes_with_headers_non_multipart_mixed_response_text(client):
    uri = "/some/dir/doc3.xqy"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
    builder.with_response_header("vnd.marklogic.document-format", "text")
    builder.with_response_status(200)
    builder.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers == {
        "vnd.marklogic.document-format": "text",
        "Content-Type": "application/vnd.marklogic-xdmp; charset=utf-8",
        "Content-Length": "43",
    }


@responses.activate
def test_parse_non_multipart_mixed_response_binary(client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/zip")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.with_response_header("vnd.marklogic.document-format", "binary")
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content


@responses.activate
def test_parse_text_non_multipart_mixed_response_binary(client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/zip")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.with_response_header("vnd.marklogic.document-format", "binary")
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content


@responses.activate
def test_parse_bytes_non_multipart_mixed_response_binary(client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/zip")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.with_response_header("vnd.marklogic.document-format", "binary")
    builder.build_get()

    resp = client.get_documents(uri=uri)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content


@responses.activate
def test_parse_with_headers_non_multipart_mixed_response_binary(client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/zip")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.with_response_header("vnd.marklogic.document-format", "binary")
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content
    assert headers == {
        "vnd.marklogic.document-format": "binary",
        "Content-Type": "application/zip",
        "Content-Length": "51",
    }


@responses.activate
def test_parse_text_with_headers_non_multipart_mixed_response_binary(client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/zip")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.with_response_header("vnd.marklogic.document-format", "binary")
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content
    assert headers == {
        "vnd.marklogic.document-format": "binary",
        "Content-Type": "application/zip",
        "Content-Length": "51",
    }


@responses.activate
def test_parse_bytes_with_headers_non_multipart_mixed_response_binary(client):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", uri)
    builder.with_response_content_type("application/zip")
    builder.with_response_status(200)
    builder.with_response_body(content)
    builder.with_response_header("vnd.marklogic.document-format", "binary")
    builder.build_get()

    resp = client.get_documents(uri=uri)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == content
    assert headers == {
        "vnd.marklogic.document-format": "binary",
        "Content-Type": "application/zip",
        "Content-Length": "51",
    }


@responses.activate
def test_parse_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.json")
    builder.with_request_param("uri", "/some/dir/doc3.xqy")
    builder.with_request_param("uri", "/some/dir/doc4.zip")
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/zip",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc4.zip"; '
                "category=content; "
                "format=binary",
                "content": zip_content,
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/vnd.marklogic-xdmp",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc3.xqy"; '
                "category=content; "
                "format=text",
                "content": b'xquery version "1.0-ml";\n\nfn:current-date()',
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/json",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc2.json"; '
                "category=content; "
                "format=json",
                "content": b'{"root": {"child": "data"}}',
            },
        ),
    )
    builder.build_get()

    resp = client.get_documents(uri=uris)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)

    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == zip_content

    assert isinstance(parsed_resp[1], ElemTree.ElementTree)
    assert parsed_resp[1].getroot().tag == "root"
    assert parsed_resp[1].getroot().text is None
    assert parsed_resp[1].getroot().attrib == {}

    assert isinstance(parsed_resp[2], str)
    assert parsed_resp[2] == 'xquery version "1.0-ml";\n\nfn:current-date()'

    assert isinstance(parsed_resp[3], dict)
    assert parsed_resp[3] == {"root": {"child": "data"}}


@responses.activate
def test_parse_text_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.json")
    builder.with_request_param("uri", "/some/dir/doc3.xqy")
    builder.with_request_param("uri", "/some/dir/doc4.zip")
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/zip",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc4.zip"; '
                "category=content; "
                "format=binary",
                "content": zip_content,
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/vnd.marklogic-xdmp",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc3.xqy"; '
                "category=content; "
                "format=text",
                "content": b'xquery version "1.0-ml";\n\nfn:current-date()',
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/json",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc2.json"; '
                "category=content; "
                "format=json",
                "content": b'{"root":{"child":"data"}}',
            },
        ),
    )
    builder.build_get()

    resp = client.get_documents(uri=uris)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, list)

    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == zip_content

    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == (
        '<?xml version="1.0" encoding="UTF-8"?>\n' "<root><child>data</child></root>"
    )

    assert isinstance(parsed_resp[2], str)
    assert parsed_resp[2] == 'xquery version "1.0-ml";\n\nfn:current-date()'

    assert isinstance(parsed_resp[3], str)
    assert parsed_resp[3] == '{"root":{"child":"data"}}'


@responses.activate
def test_parse_bytes_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.json")
    builder.with_request_param("uri", "/some/dir/doc3.xqy")
    builder.with_request_param("uri", "/some/dir/doc4.zip")
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/zip",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc4.zip"; '
                "category=content; "
                "format=binary",
                "content": zip_content,
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/vnd.marklogic-xdmp",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc3.xqy"; '
                "category=content; "
                "format=text",
                "content": b'xquery version "1.0-ml";\n\nfn:current-date()',
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/json",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc2.json"; '
                "category=content; "
                "format=json",
                "content": b'{"root":{"child":"data"}}',
            },
        ),
    )
    builder.build_get()

    resp = client.get_documents(uri=uris)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, list)

    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == zip_content

    assert isinstance(parsed_resp[1], bytes)
    assert parsed_resp[1] == (
        b'<?xml version="1.0" encoding="UTF-8"?>\n' b"<root><child>data</child></root>"
    )

    assert isinstance(parsed_resp[2], bytes)
    assert parsed_resp[2] == b'xquery version "1.0-ml";\n\nfn:current-date()'

    assert isinstance(parsed_resp[3], bytes)
    assert parsed_resp[3] == b'{"root":{"child":"data"}}'


@responses.activate
def test_parse_with_headers_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.json")
    builder.with_request_param("uri", "/some/dir/doc3.xqy")
    builder.with_request_param("uri", "/some/dir/doc4.zip")
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/zip",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc4.zip"; '
                "category=content; "
                "format=binary",
                "content": zip_content,
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/vnd.marklogic-xdmp",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc3.xqy"; '
                "category=content; "
                "format=text",
                "content": b'xquery version "1.0-ml";\n\nfn:current-date()',
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/json",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc2.json"; '
                "category=content; "
                "format=json",
                "content": b'{"root": {"child": "data"}}',
            },
        ),
    )
    builder.build_get()

    resp = client.get_documents(uri=uris)
    parsed_resp_list = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp_list, list)

    headers_1, parsed_resp_1 = parsed_resp_list[0]
    headers_2, parsed_resp_2 = parsed_resp_list[1]
    headers_3, parsed_resp_3 = parsed_resp_list[2]
    headers_4, parsed_resp_4 = parsed_resp_list[3]

    assert isinstance(parsed_resp_1, bytes)
    assert parsed_resp_1 == zip_content
    assert headers_1 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc4.zip"; category=content; format=binary',
        "Content-Type": "application/zip",
    }

    assert isinstance(parsed_resp_2, ElemTree.ElementTree)
    assert parsed_resp_2.getroot().tag == "root"
    assert parsed_resp_2.getroot().text is None
    assert parsed_resp_2.getroot().attrib == {}
    assert headers_2 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc1.xml"; category=content; format=xml',
        "Content-Type": "application/xml",
    }

    assert isinstance(parsed_resp_3, str)
    assert parsed_resp_3 == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers_3 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc3.xqy"; category=content; format=text',
        "Content-Type": "application/vnd.marklogic-xdmp",
    }

    assert isinstance(parsed_resp_4, dict)
    assert parsed_resp_4 == {"root": {"child": "data"}}
    assert headers_4 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc2.json"; category=content; format=json',
        "Content-Type": "application/json",
    }


@responses.activate
def test_parse_with_headers_text_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.json")
    builder.with_request_param("uri", "/some/dir/doc3.xqy")
    builder.with_request_param("uri", "/some/dir/doc4.zip")
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/zip",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc4.zip"; '
                "category=content; "
                "format=binary",
                "content": zip_content,
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/vnd.marklogic-xdmp",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc3.xqy"; '
                "category=content; "
                "format=text",
                "content": b'xquery version "1.0-ml";\n\nfn:current-date()',
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/json",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc2.json"; '
                "category=content; "
                "format=json",
                "content": b'{"root":{"child":"data"}}',
            },
        ),
    )
    builder.build_get()

    resp = client.get_documents(uri=uris)
    parsed_resp_list = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp_list, list)

    headers_1, parsed_resp_1 = parsed_resp_list[0]
    headers_2, parsed_resp_2 = parsed_resp_list[1]
    headers_3, parsed_resp_3 = parsed_resp_list[2]
    headers_4, parsed_resp_4 = parsed_resp_list[3]

    assert isinstance(parsed_resp_1, bytes)
    assert parsed_resp_1 == zip_content
    assert headers_1 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc4.zip"; category=content; format=binary',
        "Content-Type": "application/zip",
    }

    assert isinstance(parsed_resp_2, str)
    assert parsed_resp_2 == (
        '<?xml version="1.0" encoding="UTF-8"?>\n' "<root><child>data</child></root>"
    )
    assert headers_2 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc1.xml"; category=content; format=xml',
        "Content-Type": "application/xml",
    }

    assert isinstance(parsed_resp_3, str)
    assert parsed_resp_3 == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers_3 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc3.xqy"; category=content; format=text',
        "Content-Type": "application/vnd.marklogic-xdmp",
    }

    assert isinstance(parsed_resp_4, str)
    assert parsed_resp_4 == '{"root":{"child":"data"}}'
    assert headers_4 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc2.json"; category=content; format=json',
        "Content-Type": "application/json",
    }


@responses.activate
def test_parse_with_headers_bytes_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    zip_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/some/dir/doc1.xml")
    builder.with_request_param("uri", "/some/dir/doc2.json")
    builder.with_request_param("uri", "/some/dir/doc3.xqy")
    builder.with_request_param("uri", "/some/dir/doc4.zip")
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/zip",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc4.zip"; '
                "category=content; "
                "format=binary",
                "content": zip_content,
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc1.xml"; '
                "category=content; "
                "format=xml",
                "content": b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<root><child>data</child></root>",
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/vnd.marklogic-xdmp",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc3.xqy"; '
                "category=content; "
                "format=text",
                "content": b'xquery version "1.0-ml";\n\nfn:current-date()',
            },
        ),
    )
    builder.with_response_documents_body_part(
        DocumentsBodyPart(
            **{
                "content-type": "application/json",
                "content-disposition": "attachment; "
                'filename="/some/dir/doc2.json"; '
                "category=content; "
                "format=json",
                "content": b'{"root":{"child":"data"}}',
            },
        ),
    )
    builder.build_get()

    resp = client.get_documents(uri=uris)
    parsed_resp_list = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp_list, list)

    headers_1, parsed_resp_1 = parsed_resp_list[0]
    headers_2, parsed_resp_2 = parsed_resp_list[1]
    headers_3, parsed_resp_3 = parsed_resp_list[2]
    headers_4, parsed_resp_4 = parsed_resp_list[3]

    assert isinstance(parsed_resp_1, bytes)
    assert parsed_resp_1 == zip_content
    assert headers_1 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc4.zip"; category=content; format=binary',
        "Content-Type": "application/zip",
    }

    assert isinstance(parsed_resp_2, bytes)
    assert parsed_resp_2 == (
        b'<?xml version="1.0" encoding="UTF-8"?>\n' b"<root><child>data</child></root>"
    )
    assert headers_2 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc1.xml"; category=content; format=xml',
        "Content-Type": "application/xml",
    }

    assert isinstance(parsed_resp_3, bytes)
    assert parsed_resp_3 == b'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers_3 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc3.xqy"; category=content; format=text',
        "Content-Type": "application/vnd.marklogic-xdmp",
    }

    assert isinstance(parsed_resp_4, bytes)
    assert parsed_resp_4 == b'{"root":{"child":"data"}}'
    assert headers_4 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc2.json"; category=content; format=json',
        "Content-Type": "application/json",
    }


@responses.activate
def test_parse_single_unsupported_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'


@responses.activate
def test_parse_text_single_unsupported_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'cts:directory-query("/root/", "infinity")'


@responses.activate
def test_parse_bytes_single_unsupported_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'


@responses.activate
def test_parse_with_headers_single_unsupported_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }


@responses.activate
def test_parse_text_with_headers_single_unsupported_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'cts:directory-query("/root/", "infinity")'
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }


@responses.activate
def test_parse_bytes_with_headers_single_unsupported_response(client):
    xqy = 'cts:directory-query("/root/", "infinity")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }


@responses.activate
def test_parse_single_empty_response(client):
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


@responses.activate
def test_parse_text_single_empty_response(client):
    xqy = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_empty_response_body()
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []


@responses.activate
def test_parse_bytes_single_empty_response(client):
    xqy = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_empty_response_body()
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []


@responses.activate
def test_parse_with_headers_single_empty_response(client):
    xqy = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_empty_response_body()
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []
    assert headers == {
        "Content-Type": "text/plain",
        "Content-Length": "0",
    }


@responses.activate
def test_parse_text_with_headers_single_empty_response(client):
    xqy = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_empty_response_body()
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []
    assert headers == {
        "Content-Type": "text/plain",
        "Content-Length": "0",
    }


@responses.activate
def test_parse_bytes_with_headers_single_empty_response(client):
    xqy = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_empty_response_body()
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []
    assert headers == {
        "Content-Type": "text/plain",
        "Content-Length": "0",
    }


@responses.activate
def test_parse_single_plain_text_str_response(client):
    xqy = "'plain text'"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"


@responses.activate
def test_parse_text_single_plain_text_str_response(client):
    xqy = "'plain text'"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"


@responses.activate
def test_parse_bytes_single_plain_text_str_response(client):
    xqy = "'plain text'"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"plain text"


@responses.activate
def test_parse_with_headers_single_plain_text_str_response(client):
    xqy = "'plain text'"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }


@responses.activate
def test_parse_text_with_headers_single_plain_text_str_response(client):
    xqy = "'plain text'"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }


@responses.activate
def test_parse_bytes_with_headers_single_plain_text_str_response(client):
    xqy = "'plain text'"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"plain text"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }


@responses.activate
def test_parse_single_plain_text_int_response(client):
    xqy = "1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, int)
    assert parsed_resp == 1


@responses.activate
def test_parse_text_single_plain_text_int_response(client):
    xqy = "1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "1"


@responses.activate
def test_parse_bytes_single_plain_text_int_response(client):
    xqy = "1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"1"


@responses.activate
def test_parse_with_headers_single_plain_text_int_response(client):
    xqy = "1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, int)
    assert parsed_resp == 1
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "integer",
    }


@responses.activate
def test_parse_text_with_headers_single_plain_text_int_response(client):
    xqy = "1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "1"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "integer",
    }


@responses.activate
def test_parse_bytes_with_headers_single_plain_text_int_response(client):
    xqy = "1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"1"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "integer",
    }


@responses.activate
def test_parse_single_plain_text_decimal_response(client):
    xqy = "1.1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("decimal", "1.1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, float)
    assert parsed_resp == 1.1


@responses.activate
def test_parse_text_single_plain_text_decimal_response(client):
    xqy = "1.1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("decimal", "1.1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "1.1"


@responses.activate
def test_parse_bytes_single_plain_text_decimal_response(client):
    xqy = "1.1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("decimal", "1.1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"1.1"


@responses.activate
def test_parse_with_headers_single_plain_text_decimal_response(client):
    xqy = "1.1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("decimal", "1.1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, float)
    assert parsed_resp == 1.1
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "decimal",
    }


@responses.activate
def test_parse_text_with_headers_single_plain_text_decimal_response(client):
    xqy = "1.1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("decimal", "1.1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "1.1"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "decimal",
    }


@responses.activate
def test_parse_bytes_with_headers_single_plain_text_decimal_response(client):
    xqy = "1.1"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("decimal", "1.1")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"1.1"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "decimal",
    }


@responses.activate
def test_parse_single_plain_text_boolean_response(client):
    xqy = "fn:true()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("boolean", "true")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bool)
    assert parsed_resp is True


@responses.activate
def test_parse_text_single_plain_text_boolean_response(client):
    xqy = "fn:true()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("boolean", "true")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "true"


@responses.activate
def test_parse_bytes_single_plain_text_boolean_response(client):
    xqy = "fn:true()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("boolean", "true")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"true"


@responses.activate
def test_parse_with_headers_single_plain_text_boolean_response(client):
    xqy = "fn:true()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("boolean", "true")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, bool)
    assert parsed_resp is True
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "boolean",
    }


@responses.activate
def test_parse_text_with_headers_single_plain_text_boolean_response(client):
    xqy = "fn:true()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("boolean", "true")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "true"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "boolean",
    }


@responses.activate
def test_parse_bytes_with_headers_single_plain_text_boolean_response(client):
    xqy = "fn:true()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("boolean", "true")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"true"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "boolean",
    }


@responses.activate
def test_parse_single_plain_text_date_response(client):
    xqy = "fn:current-date()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("date", "2023-09-14Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, date)
    assert parsed_resp == datetime.strptime("2023-09-14Z", "%Y-%m-%d%z").date()


@responses.activate
def test_parse_text_single_plain_text_date_response(client):
    xqy = "fn:current-date()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("date", "2023-09-14Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "2023-09-14Z"


@responses.activate
def test_parse_bytes_single_plain_text_date_response(client):
    xqy = "fn:current-date()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("date", "2023-09-14Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"2023-09-14Z"


@responses.activate
def test_parse_with_headers_single_plain_text_date_response(client):
    xqy = "fn:current-date()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("date", "2023-09-14Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, date)
    assert parsed_resp == datetime.strptime("2023-09-14Z", "%Y-%m-%d%z").date()
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "date",
    }


@responses.activate
def test_parse_text_with_headers_single_plain_text_date_response(client):
    xqy = "fn:current-date()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("date", "2023-09-14Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "2023-09-14Z"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "date",
    }


@responses.activate
def test_parse_bytes_with_headers_single_plain_text_date_response(client):
    xqy = "fn:current-date()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("date", "2023-09-14Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"2023-09-14Z"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "date",
    }


@responses.activate
def test_parse_single_plain_text_date_time_response(client):
    xqy = "fn:current-dateTime()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("dateTime", "2023-09-14T07:30:27.997332Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, datetime)
    assert parsed_resp == datetime.strptime(
        "2023-09-14T07:30:27.997332Z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )


@responses.activate
def test_parse_text_single_plain_text_date_time_response(client):
    xqy = "fn:current-dateTime()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("dateTime", "2023-09-14T07:30:27.997332Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "2023-09-14T07:30:27.997332Z"


@responses.activate
def test_parse_bytes_single_plain_text_date_time_response(client):
    xqy = "fn:current-dateTime()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("dateTime", "2023-09-14T07:30:27.997332Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"2023-09-14T07:30:27.997332Z"


@responses.activate
def test_parse_with_headers_single_plain_text_date_time_response(client):
    xqy = "fn:current-dateTime()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("dateTime", "2023-09-14T07:30:27.997332Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, datetime)
    assert parsed_resp == datetime.strptime(
        "2023-09-14T07:30:27.997332Z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "dateTime",
    }


@responses.activate
def test_parse_text_with_headers_single_plain_text_date_time_response(client):
    xqy = "fn:current-dateTime()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("dateTime", "2023-09-14T07:30:27.997332Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "2023-09-14T07:30:27.997332Z"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "dateTime",
    }


@responses.activate
def test_parse_bytes_with_headers_single_plain_text_date_time_response(client):
    xqy = "fn:current-dateTime()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("dateTime", "2023-09-14T07:30:27.997332Z")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"2023-09-14T07:30:27.997332Z"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "dateTime",
    }


@responses.activate
def test_parse_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    )
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


@responses.activate
def test_parse_text_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("map", serialized_map)
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == serialized_map


@responses.activate
def test_parse_bytes_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("map", serialized_map)
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == serialized_map.encode("utf-8")


@responses.activate
def test_parse_with_headers_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {
        "str": "value",
        "int_str": "1",
        "int": 1,
        "float": 1.1,
        "bool": True,
    }
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


@responses.activate
def test_parse_text_with_headers_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == serialized_map
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


@responses.activate
def test_parse_bytes_with_headers_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == serialized_map.encode("utf-8")
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


@responses.activate
def test_parse_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    )
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


@responses.activate
def test_parse_text_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("map", serialized_map)
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == serialized_map


@responses.activate
def test_parse_bytes_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("map", serialized_map)
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == serialized_map.encode("utf-8")


@responses.activate
def test_parse_with_headers_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {
        "str": "value",
        "int_str": "1",
        "int": 1,
        "float": 1.1,
        "bool": True,
    }
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


@responses.activate
def test_parse_text_with_headers_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == serialized_map
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


@responses.activate
def test_parse_bytes_with_headers_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "map",
        '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == serialized_map.encode("utf-8")
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


@responses.activate
def test_parse_single_json_array_response(client):
    xqy = '("value", "1", 1, 1.1, fn:true()) => json:to-array()'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("array", '["value", "1", 1, 1.1, true]')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == ["value", "1", 1, 1.1, True]


@responses.activate
def test_parse_text_single_json_array_response(client):
    xqy = '("value", "1", 1, 1.1, fn:true()) => json:to-array()'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("array", '["value", "1", 1, 1.1, true]')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '["value", "1", 1, 1.1, true]'


@responses.activate
def test_parse_bytes_single_json_array_response(client):
    xqy = '("value", "1", 1, 1.1, fn:true()) => json:to-array()'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("array", '["value", "1", 1, 1.1, true]')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'["value", "1", 1, 1.1, true]'


@responses.activate
def test_parse_with_headers_single_json_array_response(client):
    xqy = '("value", "1", 1, 1.1, fn:true()) => json:to-array()'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("array", '["value", "1", 1, 1.1, true]')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == ["value", "1", 1, 1.1, True]
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "array",
    }


@responses.activate
def test_parse_text_with_headers_single_json_array_response(client):
    xqy = '("value", "1", 1, 1.1, fn:true()) => json:to-array()'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("array", '["value", "1", 1, 1.1, true]')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '["value", "1", 1, 1.1, true]'
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "array",
    }


@responses.activate
def test_parse_bytes_with_headers_single_json_array_response(client):
    xqy = '("value", "1", 1, 1.1, fn:true()) => json:to-array()'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("array", '["value", "1", 1, 1.1, true]')
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'["value", "1", 1, 1.1, true]'
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "array",
    }


@responses.activate
def test_parse_single_xml_document_node_response(client):
    xqy = "document { element root {} }"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "document-node()",
        '<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}


@responses.activate
def test_parse_text_single_xml_document_node_response(client):
    xqy = "document { element root {} }"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "document-node()",
        '<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'


@responses.activate
def test_parse_bytes_single_xml_document_node_response(client):
    xqy = "document { element root {} }"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "document-node()",
        '<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>'


@responses.activate
def test_parse_with_headers_single_xml_document_node_response(client):
    xqy = "document { element root {} }"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "document-node()",
        '<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "document-node()",
    }


@responses.activate
def test_parse_text_with_headers_single_xml_document_node_response(client):
    xqy = "document { element root {} }"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "document-node()",
        '<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "document-node()",
    }


@responses.activate
def test_parse_bytes_with_headers_single_xml_document_node_response(client):
    xqy = "document { element root {} }"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "document-node()",
        '<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
    )
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "document-node()",
    }


@responses.activate
def test_parse_single_xml_element_response(client):
    xqy = "element root {}"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("element()", "<root/>")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, ElemTree.Element)
    assert parsed_resp.tag == "root"
    assert parsed_resp.text is None
    assert parsed_resp.attrib == {}


@responses.activate
def test_parse_text_single_xml_element_response(client):
    xqy = "element root {}"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("element()", "<root/>")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "<root/>"


@responses.activate
def test_parse_bytes_single_xml_element_response(client):
    xqy = "element root {}"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("element()", "<root/>")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"<root/>"


@responses.activate
def test_parse_with_headers_single_xml_element_response(client):
    xqy = "element root {}"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("element()", "<root/>")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, ElemTree.Element)
    assert parsed_resp.tag == "root"
    assert parsed_resp.text is None
    assert parsed_resp.attrib == {}
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "element()",
    }


@responses.activate
def test_parse_text_with_headers_single_xml_element_response(client):
    xqy = "element root {}"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("element()", "<root/>")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "<root/>"
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "element()",
    }


@responses.activate
def test_parse_bytes_with_headers_single_xml_element_response(client):
    xqy = "element root {}"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("element()", "<root/>")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"<root/>"
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "element()",
    }


@responses.activate
def test_parse_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == b'cts:directory-query("/root/", "infinity")'
    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == "plain text"


@responses.activate
def test_parse_text_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], str)
    assert parsed_resp[0] == 'cts:directory-query("/root/", "infinity")'
    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == "plain text"


@responses.activate
def test_parse_bytes_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == b'cts:directory-query("/root/", "infinity")'
    assert isinstance(parsed_resp[1], bytes)
    assert parsed_resp[1] == b"plain text"


@responses.activate
def test_parse_with_headers_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp_with_headers = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp_with_headers, list)

    headers_1, parsed_resp_1 = parsed_resp_with_headers[0]
    assert isinstance(parsed_resp_1, bytes)
    assert parsed_resp_1 == b'cts:directory-query("/root/", "infinity")'
    assert headers_1 == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }

    headers_2, parsed_resp_2 = parsed_resp_with_headers[1]
    assert isinstance(parsed_resp_2, str)
    assert parsed_resp_2 == "plain text"
    assert headers_2 == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }


@responses.activate
def test_parse_text_with_headers_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp_with_headers = MLResponseParser.parse_with_headers(
        resp,
        output_type=str,
    )

    assert isinstance(parsed_resp_with_headers, list)

    headers_1, parsed_resp_1 = parsed_resp_with_headers[0]
    assert isinstance(parsed_resp_1, str)
    assert parsed_resp_1 == 'cts:directory-query("/root/", "infinity")'
    assert headers_1 == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }

    headers_2, parsed_resp_2 = parsed_resp_with_headers[1]
    assert isinstance(parsed_resp_2, str)
    assert parsed_resp_2 == "plain text"
    assert headers_2 == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }


@responses.activate
def test_parse_bytes_with_headers_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": xqy})
    builder.with_response_status(200)
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part(
        "directory-query",
        'cts:directory-query("/root/", "infinity")',
    )
    builder.with_response_body_part("string", "plain text")
    builder.build_post()

    resp = client.eval(xquery=xqy)
    parsed_resp_with_headers = MLResponseParser.parse_with_headers(
        resp,
        output_type=bytes,
    )

    assert isinstance(parsed_resp_with_headers, list)

    headers_1, parsed_resp_1 = parsed_resp_with_headers[0]
    assert isinstance(parsed_resp_1, bytes)
    assert parsed_resp_1 == b'cts:directory-query("/root/", "infinity")'
    assert headers_1 == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }

    headers_2, parsed_resp_2 = parsed_resp_with_headers[1]
    assert isinstance(parsed_resp_2, bytes)
    assert parsed_resp_2 == b"plain text"
    assert headers_2 == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }
