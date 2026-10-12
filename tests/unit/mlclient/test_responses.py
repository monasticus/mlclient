import xml.etree.ElementTree as ElemTree
import zlib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.models import DocumentsBodyPart
from mlclient.responses import MLResponseParser
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

ml_mocker = MLRespXMocker(router_base_url="http://localhost:8000")
ml_mock = ml_mocker.router


ml_mocker.with_name("single-text-node-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'text { "text" }'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("text()", "text", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, str, "text"),
        (str, str, "text"),
        (bytes, bytes, b"text"),
    ],
)
def test_parse_single_text_node_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery='text { "text" }')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "text/plain",
            "X-Primitive": "text()",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-attribute-node-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'attribute name { "value" }'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("attribute()", "value", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, str, "value"),
        (str, str, "value"),
        (bytes, bytes, b"value"),
    ],
)
def test_parse_single_attribute_node_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery='attribute name { "value" }')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "text/plain",
            "X-Primitive": "attribute()",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-comment-node-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'comment { "comment" }'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("comment()", "<!--comment-->", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, str, "<!--comment-->"),
        (str, str, "<!--comment-->"),
        (bytes, bytes, b"<!--comment-->"),
    ],
)
def test_parse_single_comment_node_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery='comment { "comment" }')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "text/plain",
            "X-Primitive": "comment()",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-processing-instruction-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'processing-instruction target { "value" }'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "processing-instruction()",
    "<?target value?>",
    "text/plain",
)
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, str, "<?target value?>"),
        (str, str, "<?target value?>"),
        (bytes, bytes, b"<?target value?>"),
    ],
)
def test_parse_single_processing_instruction_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery='processing-instruction target { "value" }')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "text/plain",
            "X-Primitive": "processing-instruction()",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-binary-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'binary { xs:hexBinary("62696E617279") }'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "binary()",
    "binary",
    "application/x-unknown-content-type",
)
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, bytes, b"binary"),
        (str, bytes, b"binary"),
        (bytes, bytes, b"binary"),
    ],
)
def test_parse_single_binary_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery='binary { xs:hexBinary("62696E617279") }')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "application/x-unknown-content-type",
            "X-Primitive": "binary()",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-byte-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:byte(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_byte_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:byte(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-short-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:short(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_short_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:short(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-int-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:int(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_int_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:int(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-long-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:long(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_long_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:long(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-non-positive-integer-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:nonPositiveInteger(0)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "0", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 0),
        (str, str, "0"),
        (bytes, bytes, b"0"),
    ],
)
def test_parse_single_non_positive_integer_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:nonPositiveInteger(0)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-negative-integer-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:negativeInteger(-1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "-1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, -1),
        (str, str, "-1"),
        (bytes, bytes, b"-1"),
    ],
)
def test_parse_single_negative_integer_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:negativeInteger(-1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-non-negative-integer-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:nonNegativeInteger(0)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "0", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 0),
        (str, str, "0"),
        (bytes, bytes, b"0"),
    ],
)
def test_parse_single_non_negative_integer_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:nonNegativeInteger(0)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-positive-integer-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:positiveInteger(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_positive_integer_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:positiveInteger(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-unsigned-byte-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:unsignedByte(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_unsigned_byte_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:unsignedByte(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-unsigned-short-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:unsignedShort(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_unsigned_short_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:unsignedShort(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-unsigned-int-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:unsignedInt(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_unsigned_int_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:unsignedInt(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-unsigned-long-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:unsignedLong(1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_unsigned_long_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:unsignedLong(1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-float-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:float(1.1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("float", "1.1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, float, 1.1),
        (str, str, "1.1"),
        (bytes, bytes, b"1.1"),
    ],
)
def test_parse_single_float_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:float(1.1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "float"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-double-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "xs:double(1.1)"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("double", "1.1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, float, 1.1),
        (str, str, "1.1"),
        (bytes, bytes, b"1.1"),
    ],
)
def test_parse_single_double_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="xs:double(1.1)")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "double"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


@pytest.fixture(scope="module")
def ml():
    return MLClient()


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown(ml):
    # Setup
    ml.connect()

    yield

    # Teardown
    ml.disconnect()


ml_mocker.with_name("html-error")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "'missing-quote"})
ml_mocker.with_response_code(500)
ml_mocker.with_response_content_type("text/html; charset=utf-8")
ml_mocker.with_response_header("Content-Length", "1014")
ml_mocker.with_response_body(
    resources_utils.read_test_resource_text(__file__, "error-response.html"),
)
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (
            None,
            str,
            (
                "XDMP-BADCHAR: (err:XPST0003) Unexpected character "
                "found ''' (0x0027)\nin /eval, at 1:0 [1.0-ml]"
            ),
        ),
        (
            str,
            str,
            (
                "XDMP-BADCHAR: (err:XPST0003) Unexpected character "
                "found ''' (0x0027)\nin /eval, at 1:0 [1.0-ml]"
            ),
        ),
        (
            bytes,
            bytes,
            (
                b"XDMP-BADCHAR: (err:XPST0003) Unexpected character "
                b"found ''' (0x0027)\nin /eval, at 1:0 [1.0-ml]"
            ),
        ),
    ],
)
def test_parse_error_response_html(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="'missing-quote")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": "1014",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("xml-error")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc1.xml")
ml_mocker.with_request_param("database", "Document")
ml_mocker.with_request_header("Accept", "application/xml")
ml_mocker.with_response_code(400)
ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
ml_mocker.with_response_header("Content-Length", "246")
ml_mocker.with_response_body(
    resources_utils.read_test_resource_text(__file__, "error-response.xml"),
)
ml_mocker.mock_delete()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (
            None,
            dict,
            {
                "errorResponse": {
                    "statusCode": 400,
                    "status": "Bad Request",
                    "messageCode": "XDMP-NOSUCHDB",
                    "message": "XDMP-NOSUCHDB: No such database Document",
                },
            },
        ),
        (
            str,
            str,
            (
                '{"errorResponse": {"statusCode": 400, "status'
                '": "Bad Request", "messageCode": "XDMP-NOSUCH'
                'DB", "message": "XDMP-NOSUCHDB: No such datab'
                'ase Document"}}'
            ),
        ),
        (
            bytes,
            bytes,
            (
                b'{"errorResponse": {"statusCode": 400, "status'
                b'": "Bad Request", "messageCode": "XDMP-NOSUCH'
                b'DB", "message": "XDMP-NOSUCHDB: No such datab'
                b'ase Document"}}'
            ),
        ),
    ],
)
def test_parse_error_response_xml(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.http.delete(
        "/v1/documents",
        params={"uri": "/mlclient-response-parser/doc1.xml", "database": "Document"},
        headers={"Accept": "application/xml"},
    )
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-type": "application/xml; charset=UTF-8",
            "Content-Length": "246",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("json-error")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc.xml")
ml_mocker.with_response_code(404)
ml_mocker.with_response_content_type("application/json; charset=UTF-8")
ml_mocker.with_response_header("Content-Length", "241")
ml_mocker.with_response_body(
    resources_utils.read_test_resource_text(__file__, "error-response.json"),
)
ml_mocker.mock_get()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (
            None,
            dict,
            {
                "errorResponse": {
                    "statusCode": 404,
                    "status": "Not Found",
                    "messageCode": "RESTAPI-NODOCUMENT",
                    "message": (
                        "RESTAPI-NODOCUMENT: (err:FOER0000) Resource o"
                        "r document does not exist:  category: content"
                        " message: /mlclient-response-parser/doc.xml"
                    ),
                },
            },
        ),
        (
            str,
            str,
            (
                '{"errorResponse": {"statusCode": 404, "status'
                '": "Not Found", "messageCode": "RESTAPI-NODOC'
                'UMENT", "message": "RESTAPI-NODOCUMENT: (err:'
                "FOER0000) Resource or document does not exist"
                ":  category: content message: /mlclient-respo"
                'nse-parser/doc.xml"}}'
            ),
        ),
        (
            bytes,
            bytes,
            (
                b'{"errorResponse": {"statusCode": 404, "status'
                b'": "Not Found", "messageCode": "RESTAPI-NODOC'
                b'UMENT", "message": "RESTAPI-NODOCUMENT: (err:'
                b"FOER0000) Resource or document does not exist"
                b":  category: content message: /mlclient-respo"
                b'nse-parser/doc.xml"}}'
            ),
        ),
    ],
)
def test_parse_error_response_json(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.documents.get("/mlclient-response-parser/doc.xml")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-type": "application/json; charset=UTF-8",
            "Content-Length": "241",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("non-multipart-mixed-xml")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc1.xml")
ml_mocker.with_response_code(200)
ml_mocker.with_response_header("ML-Effective-Timestamp", "17918027341463450")
ml_mocker.with_response_header("vnd.marklogic.document-format", "xml")
ml_mocker.with_response_content_type("application/xml; charset=utf-8")
ml_mocker.with_response_header("Content-Length", "47")
ml_mocker.with_response_body('<?xml version="1.0" encoding="UTF-8"?>\n<root/>\n')
ml_mocker.mock_get()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, ElemTree.ElementTree, ("root", None, {})),
        (str, str, '<?xml version="1.0" encoding="UTF-8"?>\n<root/>\n'),
        (bytes, bytes, b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>\n'),
    ],
)
def test_parse_non_multipart_mixed_response_xml(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.documents.get("/mlclient-response-parser/doc1.xml")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "ML-Effective-Timestamp": "17918027341463450",
            "vnd.marklogic.document-format": "xml",
            "Content-type": "application/xml; charset=utf-8",
            "Content-Length": "47",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    if expected_type in (ElemTree.ElementTree, ElemTree.Element):
        root = (
            parsed_resp.getroot()
            if expected_type is ElemTree.ElementTree
            else parsed_resp
        )
        assert root.tag == expected[0]
        assert root.text == expected[1]
        assert root.attrib == expected[2]
    else:
        assert parsed_resp == expected


ml_mocker.with_name("non-multipart-mixed-json")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc2.json")
ml_mocker.with_response_code(200)
ml_mocker.with_response_header("ML-Effective-Timestamp", "17918027341560460")
ml_mocker.with_response_header("vnd.marklogic.document-format", "json")
ml_mocker.with_response_content_type("application/json; charset=utf-8")
ml_mocker.with_response_header("Content-Length", "26")
ml_mocker.with_response_body('{"root":{"child":"data2"}}')
ml_mocker.mock_get()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, dict, {"root": {"child": "data2"}}),
        (str, str, '{"root":{"child":"data2"}}'),
        (bytes, bytes, b'{"root":{"child":"data2"}}'),
    ],
)
def test_parse_non_multipart_mixed_response_json(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.documents.get("/mlclient-response-parser/doc2.json")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "ML-Effective-Timestamp": "17918027341560460",
            "vnd.marklogic.document-format": "json",
            "Content-type": "application/json; charset=utf-8",
            "Content-Length": "26",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("non-multipart-mixed-text")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc3.xqy")
ml_mocker.with_response_code(200)
ml_mocker.with_response_header("ML-Effective-Timestamp", "17918027341652800")
ml_mocker.with_response_header("vnd.marklogic.document-format", "text")
ml_mocker.with_response_content_type("application/vnd.marklogic-xdmp; charset=utf-8")
ml_mocker.with_response_header("Content-Length", "43")
ml_mocker.with_response_body('xquery version "1.0-ml";\n\nfn:current-date()')
ml_mocker.mock_get()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, str, 'xquery version "1.0-ml";\n\nfn:current-date()'),
        (str, str, 'xquery version "1.0-ml";\n\nfn:current-date()'),
        (bytes, bytes, b'xquery version "1.0-ml";\n\nfn:current-date()'),
    ],
)
def test_parse_non_multipart_mixed_response_text(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.documents.get("/mlclient-response-parser/doc3.xqy")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "ML-Effective-Timestamp": "17918027341652800",
            "vnd.marklogic.document-format": "text",
            "Content-type": "application/vnd.marklogic-xdmp; charset=utf-8",
            "Content-Length": "43",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("non-multipart-mixed-binary")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc4.zip")
ml_mocker.with_response_code(200)
ml_mocker.with_response_header("ML-Effective-Timestamp", "17918027341745660")
ml_mocker.with_response_header("vnd.marklogic.document-format", "binary")
ml_mocker.with_response_content_type("application/zip")
ml_mocker.with_response_header("Content-Length", "51")
binary_document = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
ml_mocker.with_response_body(binary_document)
ml_mocker.mock_get()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, bytes, zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')),
        (str, bytes, zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')),
        (bytes, bytes, zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')),
    ],
)
def test_parse_non_multipart_mixed_response_binary(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.documents.get("/mlclient-response-parser/doc4.zip")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "ML-Effective-Timestamp": "17918027341745660",
            "vnd.marklogic.document-format": "binary",
            "Content-type": "application/zip",
            "Content-Length": "51",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("multipart-mixed")
ml_mocker.with_url("/v1/documents")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc1.xml")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc2.json")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc3.xqy")
ml_mocker.with_request_param("uri", "/mlclient-response-parser/doc4.zip")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_response_code(200)
ml_mocker.with_response_header("ML-Effective-Timestamp", "17918027341915650")
ml_mocker.with_response_documents_body_part(
    DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": (
                "attachment; "
                'filename="/mlclient-response-parser/doc2.json"; '
                "category=content; "
                "format=json"
            ),
            "content": '{"root":{"child":"data"}}',
        },
    ),
)
ml_mocker.with_response_documents_body_part(
    DocumentsBodyPart(
        **{
            "content-type": "application/xml",
            "content-disposition": (
                "attachment; "
                'filename="/mlclient-response-parser/doc1.xml"; '
                "category=content; "
                "format=xml"
            ),
            "content": (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<root><child>data</child></root>"
            ),
        },
    ),
)
ml_mocker.with_response_documents_body_part(
    DocumentsBodyPart(
        **{
            "content-type": "application/vnd.marklogic-xdmp",
            "content-disposition": (
                "attachment; "
                'filename="/mlclient-response-parser/doc3.xqy"; '
                "category=content; "
                "format=text"
            ),
            "content": 'xquery version "1.0-ml";\n\nfn:current-date()',
        },
    ),
)
ml_mocker.with_response_documents_body_part(
    DocumentsBodyPart(
        **{
            "content-type": "application/zip",
            "content-disposition": (
                "attachment; "
                'filename="/mlclient-response-parser/doc4.zip"; '
                "category=content; "
                "format=binary"
            ),
            "content": binary_document,
        },
    ),
)
ml_mocker.mock_get()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_items"),
    [
        (
            None,
            [
                (dict, {"root": {"child": "data"}}),
                (ElemTree.ElementTree, ("root", None, {})),
                (str, 'xquery version "1.0-ml";\n\nfn:current-date()'),
                (
                    bytes,
                    zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()'),
                ),
            ],
        ),
        (
            str,
            [
                (str, '{"root":{"child":"data"}}'),
                (
                    str,
                    (
                        '<?xml version="1.0" encoding="UTF-8"?>\n<root>'
                        "<child>data</child></root>"
                    ),
                ),
                (str, 'xquery version "1.0-ml";\n\nfn:current-date()'),
                (
                    bytes,
                    zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()'),
                ),
            ],
        ),
        (
            bytes,
            [
                (bytes, b'{"root":{"child":"data"}}'),
                (
                    bytes,
                    (
                        b'<?xml version="1.0" encoding="UTF-8"?>\n<root>'
                        b"<child>data</child></root>"
                    ),
                ),
                (bytes, b'xquery version "1.0-ml";\n\nfn:current-date()'),
                (
                    bytes,
                    zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()'),
                ),
            ],
        ),
    ],
)
def test_parse_multipart_mixed_response(ml, output_type, expected_items, with_headers):
    uris = [
        "/mlclient-response-parser/doc1.xml",
        "/mlclient-response-parser/doc2.json",
        "/mlclient-response-parser/doc3.xqy",
        "/mlclient-response-parser/doc4.zip",
    ]
    resp = ml.rest.documents.get(uris)
    if with_headers:
        parts = MLResponseParser.parse_with_headers(resp, output_type=output_type)
        assert isinstance(parts, list)
        assert len(parts) == len(expected_items)
        assert parts[0][0] == {
            "Content-Type": "application/json",
            "Content-Disposition": (
                "attachment; "
                'filename="/mlclient-response-parser/doc2.json"; '
                "category=content; "
                "format=json"
            ),
        }
        assert parts[1][0] == {
            "Content-Type": "application/xml",
            "Content-Disposition": (
                "attachment; "
                'filename="/mlclient-response-parser/doc1.xml"; '
                "category=content; "
                "format=xml"
            ),
        }
        assert parts[2][0] == {
            "Content-Type": "application/vnd.marklogic-xdmp",
            "Content-Disposition": (
                "attachment; "
                'filename="/mlclient-response-parser/doc3.xqy"; '
                "category=content; "
                "format=text"
            ),
        }
        assert parts[3][0] == {
            "Content-Type": "application/zip",
            "Content-Disposition": (
                "attachment; "
                'filename="/mlclient-response-parser/doc4.zip"; '
                "category=content; "
                "format=binary"
            ),
        }
        parsed_resp = [value for _, value in parts]
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, list)
    assert len(parsed_resp) == len(expected_items)
    for value, (expected_type, expected) in zip(parsed_resp, expected_items):
        assert isinstance(value, expected_type)
        if expected_type is ElemTree.ElementTree:
            assert value.getroot().tag == expected[0]
            assert value.getroot().text == expected[1]
            assert value.getroot().attrib == expected[2]
        else:
            assert value == expected


ml_mocker.with_name("single-unsupported-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'cts:directory-query("/root/", "infinity")'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "directory-query",
    'cts:directory-query("/root/", "infinity")',
    "text/plain",
)
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, bytes, b'cts:directory-query("/root/", "infinity")'),
        (str, str, 'cts:directory-query("/root/", "infinity")'),
        (bytes, bytes, b'cts:directory-query("/root/", "infinity")'),
    ],
)
def test_parse_single_unsupported_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery='cts:directory-query("/root/", "infinity")')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "text/plain",
            "X-Primitive": "directory-query",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-empty-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "()"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_header("Content-Length", "0")
ml_mocker.with_response_body("")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, list, []),
        (str, list, []),
        (bytes, list, []),
    ],
)
def test_parse_single_empty_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="()")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Length": "0"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-plain-text-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "'plain text'"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("string", "plain text", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, str, "plain text"),
        (str, str, "plain text"),
        (bytes, bytes, b"plain text"),
    ],
)
def test_parse_single_plain_text_str_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="'plain text'")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "string"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-plain-text-int-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "1"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("integer", "1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, int, 1),
        (str, str, "1"),
        (bytes, bytes, b"1"),
    ],
)
def test_parse_single_plain_text_int_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="1")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "integer"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-plain-text-decimal-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "1.1"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("decimal", "1.1", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, Decimal, Decimal("1.1")),
        (str, str, "1.1"),
        (bytes, bytes, b"1.1"),
    ],
)
def test_parse_single_plain_text_decimal_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="1.1")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "decimal"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-plain-text-boolean-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "fn:true()"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("boolean", "true", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, bool, True),
        (str, str, "true"),
        (bytes, bytes, b"true"),
    ],
)
def test_parse_single_plain_text_boolean_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="fn:true()")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "boolean"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-plain-text-false-boolean-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "fn:false()"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("boolean", "false", "text/plain")
ml_mocker.mock_post()


@ml_mock
def test_parse_single_plain_text_false_boolean_response(ml):
    resp = ml.rest.eval.post(xquery="fn:false()")
    parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, bool)
    assert parsed_resp is False


ml_mocker.with_name("single-plain-text-date-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'xs:date("2023-09-14Z")'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("date", "2023-09-14Z", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, date, datetime.strptime("2023-09-14Z", "%Y-%m-%d%z").date()),
        (str, str, "2023-09-14Z"),
        (bytes, bytes, b"2023-09-14Z"),
    ],
)
def test_parse_single_plain_text_date_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery='xs:date("2023-09-14Z")')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "date"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-plain-text-date-time-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'xs:dateTime("2023-09-14T07:30:27.997332Z")'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "dateTime",
    "2023-09-14T07:30:27.997332Z",
    "text/plain",
)
ml_mocker.mock_post()


ml_mocker.with_name("date-time-one-fraction")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_header("Content-Type", "application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'xs:dateTime("2026-01-01T10:00:00.5Z")'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("dateTime", "2026-01-01T10:00:00.5Z", "text/plain")
ml_mocker.mock_post()


ml_mocker.with_name("date-time-five-fractions-offset")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_header("Content-Type", "application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body(
    {"xquery": 'xs:dateTime("2026-01-01T10:00:00.12345+02:00")'},
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "dateTime",
    "2026-01-01T10:00:00.12345+02:00",
    "text/plain",
)
ml_mocker.mock_post()


ml_mocker.with_name("date-time-seven-fractions")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_header("Content-Type", "application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'xs:dateTime("2026-01-01T10:00:00.1234567Z")'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "dateTime",
    "2026-01-01T10:00:00.1234567Z",
    "text/plain",
)
ml_mocker.mock_post()


ml_mocker.with_name("date-time-no-fraction-no-zone")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_header("Content-Type", "application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": 'xs:dateTime("2026-01-01T10:00:00")'})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("dateTime", "2026-01-01T10:00:00", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("lexical", "expected"),
    [
        (
            "2023-09-14T07:30:27.997332Z",
            datetime(2023, 9, 14, 7, 30, 27, 997332, tzinfo=timezone.utc),
        ),
        (
            "2026-01-01T10:00:00.5Z",
            datetime(2026, 1, 1, 10, 0, 0, 500000, tzinfo=timezone.utc),
        ),
        (
            "2026-01-01T10:00:00.12345+02:00",
            datetime(2026, 1, 1, 10, 0, 0, 123450, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "2026-01-01T10:00:00.1234567Z",
            datetime(2026, 1, 1, 10, 0, 0, 123456, tzinfo=timezone.utc),
        ),
        ("2026-01-01T10:00:00", datetime(2026, 1, 1, 10, 0, 0)),
    ],
)
def test_parse_single_plain_text_date_time_response(
    ml,
    lexical,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery=f'xs:dateTime("{lexical}")')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(resp)
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "dateTime"}
    else:
        parsed_resp = MLResponseParser.parse(resp)

    assert isinstance(parsed_resp, datetime)
    assert parsed_resp == expected


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected"),
    [
        (str, "2023-09-14T07:30:27.997332Z"),
        (bytes, b"2023-09-14T07:30:27.997332Z"),
    ],
)
def test_parse_raw_single_plain_text_date_time_response(
    ml,
    output_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery='xs:dateTime("2023-09-14T07:30:27.997332Z")')
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "text/plain", "X-Primitive": "dateTime"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, output_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-map-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body(
    {
        "xquery": (
            "map:map() "
            '=> map:with("str", "value") '
            '=> map:with("int_str", "1") '
            '=> map:with("int", 1) '
            '=> map:with("float", 1.1) '
            '=> map:with("bool", fn:true())'
        ),
    },
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "map",
    '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
    "application/json",
)
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (
            None,
            dict,
            {"str": "value", "int_str": "1", "int": 1, "float": 1.1, "bool": True},
        ),
        (str, str, '{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}'),
        (
            bytes,
            bytes,
            b'{"float":1.1, "int":1, "bool":true, "str":"value", "int_str":"1"}',
        ),
    ],
)
def test_parse_single_map_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    xqy = (
        "map:map() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = ml.rest.eval.post(xquery=xqy)
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "application/json", "X-Primitive": "map"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-json-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body(
    {
        "xquery": (
            "json:object() "
            '=> map:with("str", "value") '
            '=> map:with("int_str", "1") '
            '=> map:with("int", 1) '
            '=> map:with("float", 1.1) '
            '=> map:with("bool", fn:true())'
        ),
    },
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "map",
    '{"str":"value", "int_str":"1", "int":1, "float":1.1, "bool":true}',
    "application/json",
)
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (
            None,
            dict,
            {"str": "value", "int_str": "1", "int": 1, "float": 1.1, "bool": True},
        ),
        (str, str, '{"str":"value", "int_str":"1", "int":1, "float":1.1, "bool":true}'),
        (
            bytes,
            bytes,
            b'{"str":"value", "int_str":"1", "int":1, "float":1.1, "bool":true}',
        ),
    ],
)
def test_parse_single_json_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    xqy = (
        "json:object() "
        '=> map:with("str", "value") '
        '=> map:with("int_str", "1") '
        '=> map:with("int", 1) '
        '=> map:with("float", 1.1) '
        '=> map:with("bool", fn:true())'
    )
    resp = ml.rest.eval.post(xquery=xqy)
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "application/json", "X-Primitive": "map"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-json-array-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body(
    {"xquery": '("value", "1", 1, 1.1, fn:true()) => json:to-array()'},
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "array",
    '["value", "1", 1, 1.1, true]',
    "application/json",
)
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, list, ["value", "1", 1, 1.1, True]),
        (str, str, '["value", "1", 1, 1.1, true]'),
        (bytes, bytes, b'["value", "1", 1, 1.1, true]'),
    ],
)
def test_parse_single_json_array_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    xq = '("value", "1", 1, 1.1, fn:true()) => json:to-array()'
    resp = ml.rest.eval.post(xquery=xq)
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {"Content-Type": "application/json", "X-Primitive": "array"}
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    assert parsed_resp == expected


ml_mocker.with_name("single-xml-document-node-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "document { element root {} }"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "document-node()",
    '<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
    "application/xml",
)
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, ElemTree.ElementTree, ("root", None, {})),
        (str, str, '<?xml version="1.0" encoding="UTF-8"?>\n<root/>'),
        (bytes, bytes, b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>'),
    ],
)
def test_parse_single_xml_document_node_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="document { element root {} }")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "application/xml",
            "X-Primitive": "document-node()",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    if expected_type in (ElemTree.ElementTree, ElemTree.Element):
        root = (
            parsed_resp.getroot()
            if expected_type is ElemTree.ElementTree
            else parsed_resp
        )
        assert root.tag == expected[0]
        assert root.text == expected[1]
        assert root.attrib == expected[2]
    else:
        assert parsed_resp == expected


ml_mocker.with_name("single-xml-element-response")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body({"xquery": "element root {}"})
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part("element()", "<root/>", "application/xml")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_type", "expected"),
    [
        (None, ElemTree.Element, ("root", None, {})),
        (str, str, "<root/>"),
        (bytes, bytes, b"<root/>"),
    ],
)
def test_parse_single_xml_element_response(
    ml,
    output_type,
    expected_type,
    expected,
    with_headers,
):
    resp = ml.rest.eval.post(xquery="element root {}")
    if with_headers:
        headers, parsed_resp = MLResponseParser.parse_with_headers(
            resp,
            output_type=output_type,
        )
        assert headers == {
            "Content-Type": "application/xml",
            "X-Primitive": "element()",
        }
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, expected_type)
    if expected_type in (ElemTree.ElementTree, ElemTree.Element):
        root = (
            parsed_resp.getroot()
            if expected_type is ElemTree.ElementTree
            else parsed_resp
        )
        assert root.tag == expected[0]
        assert root.text == expected[1]
        assert root.attrib == expected[2]
    else:
        assert parsed_resp == expected


ml_mocker.with_name("multiple-responses")
ml_mocker.with_url("/v1/eval")
ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
ml_mocker.with_request_header("Accept", "multipart/mixed")
ml_mocker.with_request_body(
    {"xquery": '(cts:directory-query("/root/", "infinity"), (), "plain text")'},
)
ml_mocker.with_response_code(200)
ml_mocker.with_response_body_part(
    "directory-query",
    'cts:directory-query("/root/", "infinity")',
    "text/plain",
)
ml_mocker.with_response_body_part("string", "plain text", "text/plain")
ml_mocker.mock_post()


@ml_mock
@pytest.mark.parametrize("with_headers", [False, True])
@pytest.mark.parametrize(
    ("output_type", "expected_items"),
    [
        (
            None,
            [
                (bytes, b'cts:directory-query("/root/", "infinity")'),
                (str, "plain text"),
            ],
        ),
        (
            str,
            [(str, 'cts:directory-query("/root/", "infinity")'), (str, "plain text")],
        ),
        (
            bytes,
            [
                (bytes, b'cts:directory-query("/root/", "infinity")'),
                (bytes, b"plain text"),
            ],
        ),
    ],
)
def test_parse_multiple_responses(ml, output_type, expected_items, with_headers):
    xqy = '(cts:directory-query("/root/", "infinity"), (), "plain text")'
    resp = ml.rest.eval.post(xquery=xqy)
    if with_headers:
        parts = MLResponseParser.parse_with_headers(resp, output_type=output_type)
        assert isinstance(parts, list)
        assert len(parts) == len(expected_items)
        assert parts[0][0] == {
            "Content-Type": "text/plain",
            "X-Primitive": "directory-query",
        }
        assert parts[1][0] == {"Content-Type": "text/plain", "X-Primitive": "string"}
        parsed_resp = [value for _, value in parts]
    else:
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert isinstance(parsed_resp, list)
    assert len(parsed_resp) == len(expected_items)
    for value, (expected_type, expected) in zip(parsed_resp, expected_items):
        assert isinstance(value, expected_type)
        assert value == expected


@pytest.mark.parametrize(
    ("output_type", "expected"),
    [
        (None, ""),
        (str, ""),
        (bytes, b""),
    ],
)
def test_parse_non_marklogic_error_response_yields_empty(output_type, expected):
    """A synthetic proxy error has no MarkLogic result body."""
    resp = httpx.Response(
        503,
        headers={"Content-Type": "text/html"},
        content=(
            b"<html><head><title>503 Service Temporarily Un"
            b"available</title></head></html>"
        ),
        request=httpx.Request("POST", "http://localhost:8000/v1/eval"),
    )
    parsed_resp = MLResponseParser.parse(resp, output_type=output_type)

    assert parsed_resp == expected


@ml_mock
def test_raise_for_status_passes_through_a_success_response(ml):
    resp = ml.rest.eval.post(xquery="'plain text'")

    assert MLResponseParser.raise_for_status(resp) is None


@ml_mock
def test_raise_for_status_raises_marklogic_error_for_a_described_error(ml):
    resp = ml.rest.eval.post(xquery="'missing-quote")

    with pytest.raises(MarkLogicError, match="XDMP-BADCHAR"):
        MLResponseParser.raise_for_status(resp)


def test_raise_for_status_defers_to_http_status_error_without_a_body():
    """A synthetic proxy failure preserves the HTTP error."""
    resp = httpx.Response(
        503,
        request=httpx.Request("POST", "http://localhost:8000/v1/eval"),
    )

    with pytest.raises(httpx.HTTPStatusError, match="503"):
        MLResponseParser.raise_for_status(resp)


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        (None, b""),
        ("text/plain", b"Unauthorized"),
        ("text/html", b"<html><br>Unavailable"),
        ("application/json", b""),
        ("application/json", b"{broken"),
        ("application/json", b'[{"message": "gateway"}]'),
        ("application/json", b'"gateway"'),
        ("application/json", b'{"errorResponse": null}'),
        ("application/json", b'{"errorResponse": "gateway"}'),
        ("application/json", b'{"detail": "gateway"}'),
        ("application/json", b"null"),
        ("application/json", b"{}"),
        ("application/xml", b"<broken"),
        ("application/xml", b"<error>gateway</error>"),
    ],
)
def test_raise_for_status_preserves_unrecognized_http_errors(content_type, body):
    """Synthetic malformed proxy responses must preserve the HTTP error."""
    headers = {"Content-Type": content_type} if content_type else {}
    response = httpx.Response(
        503,
        headers=headers,
        content=body,
        request=httpx.Request("POST", "http://localhost:8000/v1/eval"),
    )

    with pytest.raises(httpx.HTTPStatusError) as raised:
        MLResponseParser.raise_for_status(response)

    assert raised.value.response is response
    assert raised.value.request is response.request


@pytest.mark.parametrize("status", [200, 204, 206])
def test_raise_for_status_does_not_parse_success_bodies(status):
    """Synthetic HTTP success codes bypass error-body parsing."""
    response = httpx.Response(status, content=b"not a structured body")
    assert MLResponseParser.raise_for_status(response) is None


@ml_mock
@pytest.mark.parametrize(
    ("error_format", "message", "expected_message"),
    [
        (
            "xml",
            "XDMP-NOSUCHDB",
            "[400 Bad Request] (XDMP-NOSUCHDB) "
            "XDMP-NOSUCHDB: No such database Document",
        ),
        (
            "html",
            "XDMP-BADCHAR",
            "XDMP-BADCHAR: (err:XPST0003) Unexpected character found ''' (0x0027)\n"
            "in /eval, at 1:0 [1.0-ml]",
        ),
    ],
)
def test_raise_for_status_preserves_structured_server_errors(
    ml,
    error_format,
    message,
    expected_message,
):
    if error_format == "xml":
        response = ml.http.delete(
            "/v1/documents",
            params={
                "uri": "/mlclient-response-parser/doc1.xml",
                "database": "Document",
            },
            headers={"Accept": "application/xml"},
        )
    else:
        response = ml.rest.eval.post(xquery="'missing-quote")

    with pytest.raises(MarkLogicError, match=message) as raised:
        MLResponseParser.raise_for_status(response)

    assert str(raised.value) == expected_message


@pytest.mark.parametrize("prefix", ["", "xs:"])
@pytest.mark.parametrize(
    ("lexical", "atomic_type", "expected"),
    [
        ("42", "integer", 42),
        ("42", "byte", 42),
        ("42", "short", 42),
        ("42", "int", 42),
        ("42", "long", 42),
        ("0", "nonPositiveInteger", 0),
        ("-42", "negativeInteger", -42),
        ("0", "nonNegativeInteger", 0),
        ("42", "positiveInteger", 42),
        ("42", "unsignedByte", 42),
        ("42", "unsignedShort", 42),
        ("42", "unsignedInt", 42),
        ("42", "unsignedLong", 42),
        ("1.875", "decimal", Decimal("1.875")),
        ("1.875", "double", 1.875),
        ("1.875", "float", 1.875),
        ("true", "boolean", True),
        ("1", "boolean", True),
        ("false", "boolean", False),
        ("0", "boolean", False),
        ("2023-09-14Z", "date", date(2023, 9, 14)),
        (
            "2023-09-14T07:30:27.997332Z",
            "dateTime",
            datetime(2023, 9, 14, 7, 30, 27, 997332, tzinfo=timezone.utc),
        ),
        ("42", "string", "42"),
        ("https://example.com", "anyURI", "https://example.com"),
    ],
)
def test_parse_atomic(lexical, atomic_type, expected, prefix):
    """Cover every supported atomic type and each boolean lexical form."""
    parsed = MLResponseParser.parse_atomic(lexical, f"{prefix}{atomic_type}")

    assert type(parsed) is type(expected)
    assert parsed == expected


@pytest.mark.parametrize("prefix", ["", "xs:"])
def test_parse_atomic_preserves_unrecognized_type(prefix):
    assert MLResponseParser.parse_atomic("42", f"{prefix}unknown") == "42"
