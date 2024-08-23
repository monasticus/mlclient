import xml.etree.ElementTree as ElemTree
import zlib
from datetime import date, datetime

import pytest

from mlclient import MLResourcesClient, MLResponseParser
from mlclient.structures.calls import DocumentsBodyPart
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

RESOURCES = resources_utils.get_test_resources(__file__)
ml_mocker = MLRespXMocker(router_base_url="http://localhost:8002")
ml_mock = ml_mocker.router


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


ml_mocker.with_name("html-error")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "'missing-quote"})
ml_mocker.with_response_code(500)
ml_mocker.with_response_content_type("text/html; charset=utf-8")
ml_mocker.with_response_body(RESOURCES["error-response.html"]["bytes"])
ml_mocker.mock_post()


@ml_mock
def test_parse_error_response_html(client):
    resp = client.eval(xquery="'missing-quote")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        "XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        "in /eval, at 1:0 [1.0-ml]"
    )


@ml_mock
def test_parse_text_error_response_html(client):
    resp = client.eval(xquery="'missing-quote")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        "XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        "in /eval, at 1:0 [1.0-ml]"
    )


@ml_mock
def test_parse_bytes_error_response_html(client):
    resp = client.eval(xquery="'missing-quote")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == (
        b"XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
        b"in /eval, at 1:0 [1.0-ml]"
    )


@ml_mock
def test_parse_with_headers_error_response_html(client):
    resp = client.eval(xquery="'missing-quote")
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


@ml_mock
def test_parse_text_with_headers_error_response_html(client):
    resp = client.eval(xquery="'missing-quote")
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


@ml_mock
def test_parse_bytes_with_headers_error_response_html(client):
    resp = client.eval(xquery="'missing-quote")
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


ml_mocker.with_name("xml-error")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/some/dir/doc1.xml")
ml_mocker.with_request_param("database", "Document")
ml_mocker.with_response_code(404)
ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
ml_mocker.with_response_body(RESOURCES["error-response.xml"]["bytes"])
ml_mocker.mock_delete()


@ml_mock
def test_parse_error_response_xml(client):
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


@ml_mock
def test_parse_text_error_response_xml(client):
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


@ml_mock
def test_parse_bytes_error_response_xml(client):
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


@ml_mock
def test_parse_with_headers_error_response_xml(client):
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


@ml_mock
def test_parse_text_with_headers_error_response_xml(client):
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


@ml_mock
def test_parse_bytes_with_headers_error_response_xml(client):
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


ml_mocker.with_name("json-error")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/some/dir/doc.xml")
ml_mocker.with_response_code(404)
ml_mocker.with_response_content_type("application/json; charset=UTF-8")
ml_mocker.with_response_body(RESOURCES["error-response.json"]["json"])
ml_mocker.mock_get()


@ml_mock
def test_parse_error_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc.xml")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == RESOURCES["error-response.json"]["json"]


@ml_mock
def test_parse_text_error_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc.xml")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == (
        '{"errorResponse": {'
        '"statusCode": 404, '
        '"status": "Not Found", '
        '"messageCode": "RESTAPI-NODOCUMENT", '
        '"message": "RESTAPI-NODOCUMENT: (err:FOER0000) '
        "Resource or document does not exist:  "
        'category: content message: /some/dir/doc.xml"'
        "}}"
    )


@ml_mock
def test_parse_bytes_error_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc.xml")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == (
        b'{"errorResponse": {'
        b'"statusCode": 404, '
        b'"status": "Not Found", '
        b'"messageCode": "RESTAPI-NODOCUMENT", '
        b'"message": "RESTAPI-NODOCUMENT: (err:FOER0000) '
        b"Resource or document does not exist:  "
        b'category: content message: /some/dir/doc.xml"'
        b"}}"
    )


@ml_mock
def test_parse_with_headers_error_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc.xml")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == RESOURCES["error-response.json"]["json"]
    assert headers == {
        "Content-Type": "application/json; charset=UTF-8",
        "Content-Length": "230",
    }


@ml_mock
def test_parse_text_with_headers_error_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc.xml")
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


@ml_mock
def test_parse_bytes_with_headers_error_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc.xml")
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


ml_mocker.with_name("non-multipart-mixed-xml")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/some/dir/doc1.xml")
ml_mocker.with_response_code(200)
ml_mocker.with_response_content_type("application/xml; charset=utf-8")
ml_mocker.with_response_header("vnd.marklogic.document-format", "xml")
ml_mocker.with_response_body('<?xml version="1.0" encoding="UTF-8"?>\n<root/>')
ml_mocker.mock_get()


@ml_mock
def test_parse_non_multipart_mixed_response_xml(client):
    resp = client.get_documents(uri="/some/dir/doc1.xml")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}


@ml_mock
def test_parse_text_non_multipart_mixed_response_xml(client):
    resp = client.get_documents(uri="/some/dir/doc1.xml")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'


@ml_mock
def test_parse_bytes_non_multipart_mixed_response_xml(client):
    resp = client.get_documents(uri="/some/dir/doc1.xml")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>'


@ml_mock
def test_parse_with_headers_non_multipart_mixed_response_xml(client):
    resp = client.get_documents(uri="/some/dir/doc1.xml")
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


@ml_mock
def test_parse_text_with_headers_non_multipart_mixed_response_xml(client):
    resp = client.get_documents(uri="/some/dir/doc1.xml")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert headers == {
        "vnd.marklogic.document-format": "xml",
        "Content-Type": "application/xml; charset=utf-8",
        "Content-Length": "46",
    }


@ml_mock
def test_parse_bytes_with_headers_non_multipart_mixed_response_xml(client):
    resp = client.get_documents(uri="/some/dir/doc1.xml")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert headers == {
        "vnd.marklogic.document-format": "xml",
        "Content-Type": "application/xml; charset=utf-8",
        "Content-Length": "46",
    }


ml_mocker.with_name("non-multipart-mixed-json")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/some/dir/doc2.json")
ml_mocker.with_response_code(200)
ml_mocker.with_response_content_type("application/json; charset=utf-8")
ml_mocker.with_response_header("vnd.marklogic.document-format", "json")
ml_mocker.with_response_body('{"root":{"child":"data2"}}')
ml_mocker.mock_get()


@ml_mock
def test_parse_non_multipart_mixed_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc2.json")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {"root": {"child": "data2"}}


@ml_mock
def test_parse_text_non_multipart_mixed_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc2.json")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '{"root":{"child":"data2"}}'


@ml_mock
def test_parse_bytes_non_multipart_mixed_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc2.json")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'{"root":{"child":"data2"}}'


@ml_mock
def test_parse_with_headers_non_multipart_mixed_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc2.json")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, dict)
    assert parsed_resp == {"root": {"child": "data2"}}
    assert headers == {
        "vnd.marklogic.document-format": "json",
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": "26",
    }


@ml_mock
def test_parse_text_with_headers_non_multipart_mixed_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc2.json")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '{"root":{"child":"data2"}}'
    assert headers == {
        "vnd.marklogic.document-format": "json",
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": "26",
    }


@ml_mock
def test_parse_bytes_with_headers_non_multipart_mixed_response_json(client):
    resp = client.get_documents(uri="/some/dir/doc2.json")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'{"root":{"child":"data2"}}'
    assert headers == {
        "vnd.marklogic.document-format": "json",
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": "26",
    }


ml_mocker.with_name("non-multipart-mixed-text")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/some/dir/doc3.xqy")
ml_mocker.with_response_code(200)
ml_mocker.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
ml_mocker.with_response_header("vnd.marklogic.document-format", "text")
ml_mocker.with_response_body(b'xquery version "1.0-ml";\n\nfn:current-date()')
ml_mocker.mock_get()


@ml_mock
def test_parse_non_multipart_mixed_response_text(client):
    resp = client.get_documents(uri="/some/dir/doc3.xqy")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'xquery version "1.0-ml";\n\nfn:current-date()'


@ml_mock
def test_parse_text_non_multipart_mixed_response_text(client):
    resp = client.get_documents(uri="/some/dir/doc3.xqy")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'xquery version "1.0-ml";\n\nfn:current-date()'


@ml_mock
def test_parse_bytes_non_multipart_mixed_response_text(client):
    resp = client.get_documents(uri="/some/dir/doc3.xqy")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'xquery version "1.0-ml";\n\nfn:current-date()'


@ml_mock
def test_parse_with_headers_non_multipart_mixed_response_text(client):
    resp = client.get_documents(uri="/some/dir/doc3.xqy")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers == {
        "vnd.marklogic.document-format": "text",
        "Content-Type": "application/vnd.marklogic-xdmp; charset=utf-8",
        "Content-Length": "43",
    }


@ml_mock
def test_parse_text_with_headers_non_multipart_mixed_response_text(client):
    resp = client.get_documents(uri="/some/dir/doc3.xqy")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers == {
        "vnd.marklogic.document-format": "text",
        "Content-Type": "application/vnd.marklogic-xdmp; charset=utf-8",
        "Content-Length": "43",
    }


@ml_mock
def test_parse_bytes_with_headers_non_multipart_mixed_response_text(client):
    resp = client.get_documents(uri="/some/dir/doc3.xqy")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'xquery version "1.0-ml";\n\nfn:current-date()'
    assert headers == {
        "vnd.marklogic.document-format": "text",
        "Content-Type": "application/vnd.marklogic-xdmp; charset=utf-8",
        "Content-Length": "43",
    }


ml_mocker.with_name("non-multipart-mixed-binary")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/some/dir/doc4.zip")
ml_mocker.with_response_code(200)
ml_mocker.with_response_content_type("application/zip")
ml_mocker.with_response_header("vnd.marklogic.document-format", "binary")
ml_mocker.with_response_body(
    zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()'),
)
ml_mocker.mock_get()


@ml_mock
def test_parse_non_multipart_mixed_response_binary(client):
    resp = client.get_documents(uri="/some/dir/doc4.zip")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )


@ml_mock
def test_parse_text_non_multipart_mixed_response_binary(client):
    resp = client.get_documents(uri="/some/dir/doc4.zip")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )


@ml_mock
def test_parse_bytes_non_multipart_mixed_response_binary(client):
    resp = client.get_documents(uri="/some/dir/doc4.zip")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )


@ml_mock
def test_parse_with_headers_non_multipart_mixed_response_binary(client):
    resp = client.get_documents(uri="/some/dir/doc4.zip")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )
    assert headers == {
        "vnd.marklogic.document-format": "binary",
        "Content-Type": "application/zip",
        "Content-Length": "51",
    }


@ml_mock
def test_parse_text_with_headers_non_multipart_mixed_response_binary(client):
    resp = client.get_documents(uri="/some/dir/doc4.zip")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )
    assert headers == {
        "vnd.marklogic.document-format": "binary",
        "Content-Type": "application/zip",
        "Content-Length": "51",
    }


@ml_mock
def test_parse_bytes_with_headers_non_multipart_mixed_response_binary(client):
    resp = client.get_documents(uri="/some/dir/doc4.zip")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )
    assert headers == {
        "vnd.marklogic.document-format": "binary",
        "Content-Type": "application/zip",
        "Content-Length": "51",
    }


ml_mocker.with_name("multipart-mixed")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/some/dir/doc1.xml")
ml_mocker.with_request_param("uri", "/some/dir/doc2.json")
ml_mocker.with_request_param("uri", "/some/dir/doc3.xqy")
ml_mocker.with_request_param("uri", "/some/dir/doc4.zip")
ml_mocker.with_response_code(200)
ml_mocker.with_response_documents_body_part(
    DocumentsBodyPart(
        **{
            "content-type": "application/zip",
            "content-disposition": "attachment; "
            'filename="/some/dir/doc4.zip"; '
            "category=content; "
            "format=binary",
            "content": zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()'),
        },
    ),
)
ml_mocker.with_response_documents_body_part(
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
ml_mocker.with_response_documents_body_part(
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
ml_mocker.with_response_documents_body_part(
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
ml_mocker.mock_get()


@ml_mock
def test_parse_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    resp = client.get_documents(uri=uris)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)

    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )

    assert isinstance(parsed_resp[1], ElemTree.ElementTree)
    assert parsed_resp[1].getroot().tag == "root"
    assert parsed_resp[1].getroot().text is None
    assert parsed_resp[1].getroot().attrib == {}

    assert isinstance(parsed_resp[2], str)
    assert parsed_resp[2] == 'xquery version "1.0-ml";\n\nfn:current-date()'

    assert isinstance(parsed_resp[3], dict)
    assert parsed_resp[3] == {"root": {"child": "data"}}


@ml_mock
def test_parse_text_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    resp = client.get_documents(uri=uris)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, list)

    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )

    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == (
        '<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )

    assert isinstance(parsed_resp[2], str)
    assert parsed_resp[2] == 'xquery version "1.0-ml";\n\nfn:current-date()'

    assert isinstance(parsed_resp[3], str)
    assert parsed_resp[3] == '{"root":{"child":"data"}}'


@ml_mock
def test_parse_bytes_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    resp = client.get_documents(uri=uris)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, list)

    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )

    assert isinstance(parsed_resp[1], bytes)
    assert parsed_resp[1] == (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )

    assert isinstance(parsed_resp[2], bytes)
    assert parsed_resp[2] == b'xquery version "1.0-ml";\n\nfn:current-date()'

    assert isinstance(parsed_resp[3], bytes)
    assert parsed_resp[3] == b'{"root":{"child":"data"}}'


@ml_mock
def test_parse_with_headers_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    resp = client.get_documents(uri=uris)
    parsed_resp_list = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp_list, list)

    headers_1, parsed_resp_1 = parsed_resp_list[0]
    headers_2, parsed_resp_2 = parsed_resp_list[1]
    headers_3, parsed_resp_3 = parsed_resp_list[2]
    headers_4, parsed_resp_4 = parsed_resp_list[3]

    assert isinstance(parsed_resp_1, bytes)
    assert parsed_resp_1 == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )
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


@ml_mock
def test_parse_with_headers_text_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    resp = client.get_documents(uri=uris)
    parsed_resp_list = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp_list, list)

    headers_1, parsed_resp_1 = parsed_resp_list[0]
    headers_2, parsed_resp_2 = parsed_resp_list[1]
    headers_3, parsed_resp_3 = parsed_resp_list[2]
    headers_4, parsed_resp_4 = parsed_resp_list[3]

    assert isinstance(parsed_resp_1, bytes)
    assert parsed_resp_1 == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )
    assert headers_1 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc4.zip"; category=content; format=binary',
        "Content-Type": "application/zip",
    }

    assert isinstance(parsed_resp_2, str)
    assert parsed_resp_2 == (
        '<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
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


@ml_mock
def test_parse_with_headers_bytes_multipart_mixed_response(client):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    resp = client.get_documents(uri=uris)
    parsed_resp_list = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp_list, list)

    headers_1, parsed_resp_1 = parsed_resp_list[0]
    headers_2, parsed_resp_2 = parsed_resp_list[1]
    headers_3, parsed_resp_3 = parsed_resp_list[2]
    headers_4, parsed_resp_4 = parsed_resp_list[3]

    assert isinstance(parsed_resp_1, bytes)
    assert parsed_resp_1 == zlib.compress(
        b'xquery version "1.0-ml";\n\nfn:current-date()',
    )
    assert headers_1 == {
        "Content-Disposition": "attachment; "
        'filename="/some/dir/doc4.zip"; category=content; format=binary',
        "Content-Type": "application/zip",
    }

    assert isinstance(parsed_resp_2, bytes)
    assert parsed_resp_2 == (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
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


ml_mocker.with_name("single-unsupported-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": 'cts:directory-query("/root/", "infinity")'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "directory-query",
    'cts:directory-query("/root/", "infinity")',
)
ml_mocker.mock_post()


@ml_mock
def test_parse_single_unsupported_response(client):
    resp = client.eval(xquery='cts:directory-query("/root/", "infinity")')
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'


@ml_mock
def test_parse_text_single_unsupported_response(client):
    resp = client.eval(xquery='cts:directory-query("/root/", "infinity")')
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'cts:directory-query("/root/", "infinity")'


@ml_mock
def test_parse_bytes_single_unsupported_response(client):
    resp = client.eval(xquery='cts:directory-query("/root/", "infinity")')
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'


@ml_mock
def test_parse_with_headers_single_unsupported_response(client):
    resp = client.eval(xquery='cts:directory-query("/root/", "infinity")')
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }


@ml_mock
def test_parse_text_with_headers_single_unsupported_response(client):
    resp = client.eval(xquery='cts:directory-query("/root/", "infinity")')
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == 'cts:directory-query("/root/", "infinity")'
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }


@ml_mock
def test_parse_bytes_with_headers_single_unsupported_response(client):
    resp = client.eval(xquery='cts:directory-query("/root/", "infinity")')
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'cts:directory-query("/root/", "infinity")'
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "directory-query",
    }


ml_mocker.with_name("single-empty-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "()"})
ml_mocker.with_response_code(200)
ml_mocker.with_empty_response_body()
ml_mocker.mock_post()


@ml_mock
def test_parse_single_empty_response(client):
    resp = client.eval(xquery="()")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []


@ml_mock
def test_parse_text_single_empty_response(client):
    resp = client.eval(xquery="()")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []


@ml_mock
def test_parse_bytes_single_empty_response(client):
    resp = client.eval(xquery="()")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []


@ml_mock
def test_parse_with_headers_single_empty_response(client):
    resp = client.eval(xquery="()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []
    assert headers == {
        "Content-Length": "0",
    }


@ml_mock
def test_parse_text_with_headers_single_empty_response(client):
    resp = client.eval(xquery="()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []
    assert headers == {
        "Content-Length": "0",
    }


@ml_mock
def test_parse_bytes_with_headers_single_empty_response(client):
    resp = client.eval(xquery="()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == []
    assert headers == {
        "Content-Length": "0",
    }


ml_mocker.with_name("single-plain-text-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "'plain text'"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("string", "plain text")
ml_mocker.mock_post()


@ml_mock
def test_parse_single_plain_text_str_response(client):
    resp = client.eval(xquery="'plain text'")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"


@ml_mock
def test_parse_text_single_plain_text_str_response(client):
    resp = client.eval(xquery="'plain text'")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"


@ml_mock
def test_parse_bytes_single_plain_text_str_response(client):
    resp = client.eval(xquery="'plain text'")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"plain text"


@ml_mock
def test_parse_with_headers_single_plain_text_str_response(client):
    resp = client.eval(xquery="'plain text'")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }


@ml_mock
def test_parse_text_with_headers_single_plain_text_str_response(client):
    resp = client.eval(xquery="'plain text'")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "plain text"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }


@ml_mock
def test_parse_bytes_with_headers_single_plain_text_str_response(client):
    resp = client.eval(xquery="'plain text'")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"plain text"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "string",
    }


ml_mocker.with_name("single-plain-text-int-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "1"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1")
ml_mocker.mock_post()


@ml_mock
def test_parse_single_plain_text_int_response(client):
    resp = client.eval(xquery="1")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, int)
    assert parsed_resp == 1


@ml_mock
def test_parse_text_single_plain_text_int_response(client):
    resp = client.eval(xquery="1")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "1"


@ml_mock
def test_parse_bytes_single_plain_text_int_response(client):
    resp = client.eval(xquery="1")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"1"


@ml_mock
def test_parse_with_headers_single_plain_text_int_response(client):
    resp = client.eval(xquery="1")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, int)
    assert parsed_resp == 1
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "integer",
    }


@ml_mock
def test_parse_text_with_headers_single_plain_text_int_response(client):
    resp = client.eval(xquery="1")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "1"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "integer",
    }


@ml_mock
def test_parse_bytes_with_headers_single_plain_text_int_response(client):
    resp = client.eval(xquery="1")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"1"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "integer",
    }


ml_mocker.with_name("single-plain-text-decimal-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "1.1"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("decimal", "1.1")
ml_mocker.mock_post()


@ml_mock
def test_parse_single_plain_text_decimal_response(client):
    resp = client.eval(xquery="1.1")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, float)
    assert parsed_resp == 1.1


@ml_mock
def test_parse_text_single_plain_text_decimal_response(client):
    resp = client.eval(xquery="1.1")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "1.1"


@ml_mock
def test_parse_bytes_single_plain_text_decimal_response(client):
    resp = client.eval(xquery="1.1")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"1.1"


@ml_mock
def test_parse_with_headers_single_plain_text_decimal_response(client):
    resp = client.eval(xquery="1.1")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, float)
    assert parsed_resp == 1.1
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "decimal",
    }


@ml_mock
def test_parse_text_with_headers_single_plain_text_decimal_response(client):
    resp = client.eval(xquery="1.1")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "1.1"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "decimal",
    }


@ml_mock
def test_parse_bytes_with_headers_single_plain_text_decimal_response(client):
    resp = client.eval(xquery="1.1")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"1.1"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "decimal",
    }


ml_mocker.with_name("single-plain-text-boolean-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "fn:true()"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("boolean", "true")
ml_mocker.mock_post()


@ml_mock
def test_parse_single_plain_text_boolean_response(client):
    resp = client.eval(xquery="fn:true()")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bool)
    assert parsed_resp is True


@ml_mock
def test_parse_text_single_plain_text_boolean_response(client):
    resp = client.eval(xquery="fn:true()")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "true"


@ml_mock
def test_parse_bytes_single_plain_text_boolean_response(client):
    resp = client.eval(xquery="fn:true()")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"true"


@ml_mock
def test_parse_with_headers_single_plain_text_boolean_response(client):
    resp = client.eval(xquery="fn:true()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, bool)
    assert parsed_resp is True
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "boolean",
    }


@ml_mock
def test_parse_text_with_headers_single_plain_text_boolean_response(client):
    resp = client.eval(xquery="fn:true()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "true"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "boolean",
    }


@ml_mock
def test_parse_bytes_with_headers_single_plain_text_boolean_response(client):
    resp = client.eval(xquery="fn:true()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"true"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "boolean",
    }


ml_mocker.with_name("single-plain-text-date-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "fn:current-date()"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("date", "2023-09-14Z")
ml_mocker.mock_post()


@ml_mock
def test_parse_single_plain_text_date_response(client):
    resp = client.eval(xquery="fn:current-date()")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, date)
    assert parsed_resp == datetime.strptime("2023-09-14Z", "%Y-%m-%d%z").date()


@ml_mock
def test_parse_text_single_plain_text_date_response(client):
    resp = client.eval(xquery="fn:current-date()")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "2023-09-14Z"


@ml_mock
def test_parse_bytes_single_plain_text_date_response(client):
    resp = client.eval(xquery="fn:current-date()")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"2023-09-14Z"


@ml_mock
def test_parse_with_headers_single_plain_text_date_response(client):
    resp = client.eval(xquery="fn:current-date()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, date)
    assert parsed_resp == datetime.strptime("2023-09-14Z", "%Y-%m-%d%z").date()
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "date",
    }


@ml_mock
def test_parse_text_with_headers_single_plain_text_date_response(client):
    resp = client.eval(xquery="fn:current-date()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "2023-09-14Z"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "date",
    }


@ml_mock
def test_parse_bytes_with_headers_single_plain_text_date_response(client):
    resp = client.eval(xquery="fn:current-date()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"2023-09-14Z"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "date",
    }


ml_mocker.with_name("single-plain-text-date-time-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "fn:current-dateTime()"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("dateTime", "2023-09-14T07:30:27.997332Z")
ml_mocker.mock_post()


@ml_mock
def test_parse_single_plain_text_date_time_response(client):
    resp = client.eval(xquery="fn:current-dateTime()")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, datetime)
    assert parsed_resp == datetime.strptime(
        "2023-09-14T07:30:27.997332Z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )


@ml_mock
def test_parse_text_single_plain_text_date_time_response(client):
    resp = client.eval(xquery="fn:current-dateTime()")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "2023-09-14T07:30:27.997332Z"


@ml_mock
def test_parse_bytes_single_plain_text_date_time_response(client):
    resp = client.eval(xquery="fn:current-dateTime()")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"2023-09-14T07:30:27.997332Z"


@ml_mock
def test_parse_with_headers_single_plain_text_date_time_response(client):
    resp = client.eval(xquery="fn:current-dateTime()")
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


@ml_mock
def test_parse_text_with_headers_single_plain_text_date_time_response(client):
    resp = client.eval(xquery="fn:current-dateTime()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "2023-09-14T07:30:27.997332Z"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "dateTime",
    }


@ml_mock
def test_parse_bytes_with_headers_single_plain_text_date_time_response(client):
    resp = client.eval(xquery="fn:current-dateTime()")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"2023-09-14T07:30:27.997332Z"
    assert headers == {
        "Content-Type": "text/plain",
        "X-Primitive": "dateTime",
    }


ml_mocker.with_name("single-map-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body(
    {
        "xquery": "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())',
    },
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "map",
    '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
)
ml_mocker.mock_post()


@ml_mock
def test_parse_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
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


@ml_mock
def test_parse_text_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'
    assert isinstance(parsed_resp, str)
    assert parsed_resp == serialized_map


@ml_mock
def test_parse_bytes_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'
    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == serialized_map.encode("utf-8")


@ml_mock
def test_parse_with_headers_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
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


@ml_mock
def test_parse_text_with_headers_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'
    assert isinstance(parsed_resp, str)
    assert parsed_resp == serialized_map
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


@ml_mock
def test_parse_bytes_with_headers_single_map_response(client):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'
    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == serialized_map.encode("utf-8")
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


ml_mocker.with_name("single-json-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body(
    {
        "xquery": "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())',
    },
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "map",
    '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
)
ml_mocker.mock_post()


@ml_mock
def test_parse_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
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


@ml_mock
def test_parse_text_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'
    assert isinstance(parsed_resp, str)
    assert parsed_resp == serialized_map


@ml_mock
def test_parse_bytes_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'
    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == serialized_map.encode("utf-8")


@ml_mock
def test_parse_with_headers_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
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


@ml_mock
def test_parse_text_with_headers_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'
    assert isinstance(parsed_resp, str)
    assert parsed_resp == serialized_map
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


@ml_mock
def test_parse_bytes_with_headers_single_json_response(client):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = client.eval(xquery=xqy)
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    serialized_map = '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'
    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == serialized_map.encode("utf-8")
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "map",
    }


ml_mocker.with_name("single-json-array-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body(
    {"xquery": '("value", "1", 1, 1.1, fn:true()) => json:to-array()'},
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("array", '["value", "1", 1, 1.1, true]')
ml_mocker.mock_post()


@ml_mock
def test_parse_single_json_array_response(client):
    resp = client.eval(xquery='("value", "1", 1, 1.1, fn:true()) => json:to-array()')
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == ["value", "1", 1, 1.1, True]


@ml_mock
def test_parse_text_single_json_array_response(client):
    resp = client.eval(xquery='("value", "1", 1, 1.1, fn:true()) => json:to-array()')
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '["value", "1", 1, 1.1, true]'


@ml_mock
def test_parse_bytes_single_json_array_response(client):
    resp = client.eval(xquery='("value", "1", 1, 1.1, fn:true()) => json:to-array()')
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'["value", "1", 1, 1.1, true]'


@ml_mock
def test_parse_with_headers_single_json_array_response(client):
    resp = client.eval(xquery='("value", "1", 1, 1.1, fn:true()) => json:to-array()')
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, list)
    assert parsed_resp == ["value", "1", 1, 1.1, True]
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "array",
    }


@ml_mock
def test_parse_text_with_headers_single_json_array_response(client):
    resp = client.eval(xquery='("value", "1", 1, 1.1, fn:true()) => json:to-array()')
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '["value", "1", 1, 1.1, true]'
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "array",
    }


@ml_mock
def test_parse_bytes_with_headers_single_json_array_response(client):
    resp = client.eval(xquery='("value", "1", 1, 1.1, fn:true()) => json:to-array()')
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'["value", "1", 1, 1.1, true]'
    assert headers == {
        "Content-Type": "application/json",
        "X-Primitive": "array",
    }


ml_mocker.with_name("single-xml-document-node-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "document { element root {} }"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "document-node()",
    '<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
)
ml_mocker.mock_post()


@ml_mock
def test_parse_single_xml_document_node_response(client):
    resp = client.eval(xquery="document { element root {} }")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}


@ml_mock
def test_parse_text_single_xml_document_node_response(client):
    resp = client.eval(xquery="document { element root {} }")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'


@ml_mock
def test_parse_bytes_single_xml_document_node_response(client):
    resp = client.eval(xquery="document { element root {} }")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>'


@ml_mock
def test_parse_with_headers_single_xml_document_node_response(client):
    resp = client.eval(xquery="document { element root {} }")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, ElemTree.ElementTree)
    assert parsed_resp.getroot().tag == "root"
    assert parsed_resp.getroot().text is None
    assert parsed_resp.getroot().attrib == {}
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "document-node()",
    }


@ml_mock
def test_parse_text_with_headers_single_xml_document_node_response(client):
    resp = client.eval(xquery="document { element root {} }")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "document-node()",
    }


@ml_mock
def test_parse_bytes_with_headers_single_xml_document_node_response(client):
    resp = client.eval(xquery="document { element root {} }")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>'
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "document-node()",
    }


ml_mocker.with_name("single-xml-element-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body({"xquery": "element root {}"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("element()", "<root/>")
ml_mocker.mock_post()


@ml_mock
def test_parse_single_xml_element_response(client):
    resp = client.eval(xquery="element root {}")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, ElemTree.Element)
    assert parsed_resp.tag == "root"
    assert parsed_resp.text is None
    assert parsed_resp.attrib == {}


@ml_mock
def test_parse_text_single_xml_element_response(client):
    resp = client.eval(xquery="element root {}")
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "<root/>"


@ml_mock
def test_parse_bytes_single_xml_element_response(client):
    resp = client.eval(xquery="element root {}")
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"<root/>"


@ml_mock
def test_parse_with_headers_single_xml_element_response(client):
    resp = client.eval(xquery="element root {}")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp)

    assert isinstance(parsed_resp, ElemTree.Element)
    assert parsed_resp.tag == "root"
    assert parsed_resp.text is None
    assert parsed_resp.attrib == {}
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "element()",
    }


@ml_mock
def test_parse_text_with_headers_single_xml_element_response(client):
    resp = client.eval(xquery="element root {}")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=str)

    assert isinstance(parsed_resp, str)
    assert parsed_resp == "<root/>"
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "element()",
    }


@ml_mock
def test_parse_bytes_with_headers_single_xml_element_response(client):
    resp = client.eval(xquery="element root {}")
    headers, parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)

    assert isinstance(parsed_resp, bytes)
    assert parsed_resp == b"<root/>"
    assert headers == {
        "Content-Type": "application/xml",
        "X-Primitive": "element()",
    }


ml_mocker.with_name("multiple-responses")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_body(
    {"xquery": '(cts:directory-query("/root/", "infinity"), (), "plain text")'},
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "directory-query",
    'cts:directory-query("/root/", "infinity")',
)
ml_mocker.with_response_body_part("string", "plain text")
ml_mocker.mock_post()


@ml_mock
def test_parse_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == b'cts:directory-query("/root/", "infinity")'
    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == "plain text"


@ml_mock
def test_parse_text_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=str)

    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], str)
    assert parsed_resp[0] == 'cts:directory-query("/root/", "infinity")'
    assert isinstance(parsed_resp[1], str)
    assert parsed_resp[1] == "plain text"


@ml_mock
def test_parse_bytes_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'
    resp = client.eval(xquery=xqy)
    parsed_resp = MLResponseParser.parse(resp, output_type=bytes)

    assert isinstance(parsed_resp, list)
    assert isinstance(parsed_resp[0], bytes)
    assert parsed_resp[0] == b'cts:directory-query("/root/", "infinity")'
    assert isinstance(parsed_resp[1], bytes)
    assert parsed_resp[1] == b"plain text"


@ml_mock
def test_parse_with_headers_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'
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


@ml_mock
def test_parse_text_with_headers_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'
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


@ml_mock
def test_parse_bytes_with_headers_multiple_responses(client):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'
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
