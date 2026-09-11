from __future__ import annotations

import errno
from pathlib import Path

import pytest
import respx
from cleo.testers.command_tester import CommandTester
from httpx import HTTPStatusError

from mlclient import MLEnvironment
from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import WrongParametersError
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

_BODY = "<request>payload</request>"


@pytest.fixture(autouse=True)
def ml_config() -> MLEnvironment:
    config = {
        "app-name": "my-marklogic-app",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
        "app-servers": [
            {
                "id": "manage",
                "port": 8002,
                "auth": "basic",
                "rest": True,
            },
            {
                "id": "content",
                "port": 8100,
                "auth": "basic",
            },
        ],
    }
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config):
    target = "mlclient.ml_environment.MLEnvironment.load"
    mocker.patch(target, return_value=ml_config)


@respx.mock
def test_command_http_get_writes_response_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body('{"host-default-list": {}}')
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test GET /manage/v2/hosts")
    command_output = tester.io.fetch_output()

    assert tester.command.argument("method") == "GET"
    assert tester.command.argument("endpoint") == "/manage/v2/hosts"
    assert tester.command.argument("params") == []
    assert tester.command.option("environment") == "test"
    assert tester.command.option("connection") is None
    assert command_output == '{"host-default-list": {}}\n'


@respx.mock
def test_command_http_lowercase_method_is_accepted():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body("")
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test get /manage/v2/hosts")

    assert tester.command.argument("method") == "get"


@respx.mock
def test_command_http_forwards_query_params_and_headers():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_request_param("view", "status")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body('{"host-status-list": {}}')
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute(
        "-e test GET /manage/v2/hosts view=status format=json Accept:application/json",
    )

    assert tester.command.argument("params") == [
        "view=status",
        "format=json",
        "Accept:application/json",
    ]


@respx.mock
def test_command_http_preserves_repeated_and_embedded_query_parameters():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("uri", "/one.xml")
    ml_mocker.with_request_param("uri", "/two.xml")
    ml_mocker.with_request_param("uri", "/three.xml")
    ml_mocker.with_request_param("category", "content")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body("result")
    ml_mocker.mock_get()

    tester = _get_tester()
    assert tester.execute(
        "GET /v1/documents?uri=/one.xml uri=/two.xml uri=/three.xml category=content",
    ) == 0


@respx.mock
def test_command_http_custom_rest_server():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body("")
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test -c manage GET /manage/v2/hosts")

    assert tester.command.option("connection") == "manage"


@respx.mock
def test_command_http_include_flag_prepends_status_and_headers():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", "application/json")
    ml_mocker.with_response_body('{"host-default-list": {}}')
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test -i GET /manage/v2/hosts")
    command_output = tester.io.fetch_output()

    assert tester.command.option("include") is True
    assert command_output.startswith("HTTP/1.1 200 OK\n")
    assert '{"host-default-list": {}}' in command_output


@respx.mock
def test_command_http_displays_redirect_without_treating_it_as_failure():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_response_code(303)
    ml_mocker.with_response_header("Location", "/elsewhere")
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    tester = _get_tester()
    assert tester.execute("-i POST /v1/documents") == 0
    assert "303 See Other" in tester.io.fetch_output()


@respx.mock
def test_command_http_error_status_raises():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/nope")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body("")
    ml_mocker.mock_get()

    tester = _get_tester()
    with pytest.raises(HTTPStatusError):
        tester.execute("-e test GET /manage/v2/nope")


@respx.mock
def test_command_http_include_flag_prints_response_before_raising():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/nope")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body('{"errorResponse": {}}')
    ml_mocker.mock_get()

    tester = _get_tester()
    with pytest.raises(HTTPStatusError):
        tester.execute("-e test -i GET /manage/v2/nope")

    command_output = tester.io.fetch_output()
    assert command_output.startswith("HTTP/1.1 404 Not Found\n")
    assert '{"errorResponse": {}}' in command_output


@respx.mock
def test_command_http_pretty_indents_json_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", "application/json")
    ml_mocker.with_response_body('{"a": {"b": 1}}')
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test -p GET /manage/v2/hosts")

    assert tester.command.option("pretty") is True
    assert tester.io.fetch_output() == '{\n  "a": {\n    "b": 1\n  }\n}\n'


@respx.mock
def test_command_http_pretty_reindents_xml_without_blank_lines():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", "application/xml")
    ml_mocker.with_response_body("<a>\n  <b>\n    <c>1</c>\n  </b>\n</a>")
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test -p GET /manage/v2/hosts")
    command_output = tester.io.fetch_output()

    assert "<a>\n  <b>\n    <c>1</c>\n  </b>\n</a>" in command_output
    assert "\n\n" not in command_output


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("application/json", "broken json"),
        ("application/xml", "<broken>"),
        ("application/xml", "<p>Hello <b>world</b>!</p>"),
        ("application/xml", '<a xml:space="preserve">  <b/>  </a>'),
    ],
)
@respx.mock
def test_command_http_pretty_preserves_unformattable_body(content_type, body):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(content_type)
    ml_mocker.with_response_body(body)
    ml_mocker.mock_get()

    tester = _get_tester()
    assert tester.execute("-p GET /v1/documents") == 0
    assert tester.io.fetch_output() == body + "\n"


@respx.mock
def test_command_http_pretty_leaves_non_structured_body_untouched():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", "text/plain")
    ml_mocker.with_response_body("just text")
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test -p GET /manage/v2/hosts")

    assert tester.io.fetch_output() == "just text\n"


@respx.mock
def test_command_http_pretty_tolerates_empty_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", "application/json")
    ml_mocker.with_response_body("")
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test -p GET /manage/v2/hosts")

    assert tester.io.fetch_output() == "\n"


@respx.mock
def test_command_http_head_renders_status_and_headers():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", "application/json")
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    tester = _get_tester()
    tester.execute("-e test HEAD /manage/v2/hosts")
    command_output = tester.io.fetch_output()

    assert command_output.startswith("HTTP/1.1 200 OK\n")
    assert "content-type: application/json" in command_output


@respx.mock
def test_command_http_post_raw_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_body(_BODY)
    ml_mocker.with_response_code(201)
    ml_mocker.with_response_body("")
    ml_mocker.mock_post()

    tester = _get_tester()
    tester.execute(f"-e test POST /v1/documents -b '{_BODY}'")

    assert tester.command.argument("method") == "POST"
    assert tester.command.option("body") == _BODY


@pytest.mark.parametrize("header", ["Content-Type", "content-type"])
@respx.mock
def test_command_http_sends_literal_json_without_encoding_it_again(header):
    body = '{"value": "zażółć"}'
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_body(body.encode())
    ml_mocker.with_request_header("Content-Type", "application/json")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    tester = _get_tester()
    assert tester.execute(
        f"POST /v1/documents {header}:application/json -b '{body}'",
    ) == 0


@respx.mock
def test_command_http_accepts_body_longer_than_a_file_name():
    body = "x" * 1024
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_body(body)
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    assert _get_tester().execute(f"PUT /v1/documents -b {body}") == 0


@respx.mock
def test_command_http_post_body_from_file_path():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_body(_BODY)
    ml_mocker.with_response_code(201)
    ml_mocker.with_response_body("")
    ml_mocker.mock_post()

    body_path = resources_utils.get_test_resource_path(__file__, "body.xml")
    tester = _get_tester()
    tester.execute(f"-e test POST /v1/documents -b {body_path}")

    assert tester.command.option("body") == body_path


@respx.mock
def test_command_http_post_body_from_at_prefixed_file():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_body(_BODY)
    ml_mocker.with_response_code(201)
    ml_mocker.with_response_body("")
    ml_mocker.mock_post()

    body_path = resources_utils.get_test_resource_path(__file__, "body.xml")
    tester = _get_tester()
    tester.execute(f"-e test POST /v1/documents -b @{body_path}")

    assert tester.command.option("body") == f"@{body_path}"


@respx.mock
def test_command_http_reads_binary_body_without_decoding(tmp_path):
    body = b"\x00\xff\r\n\x80"
    path = tmp_path / "body.bin"
    path.write_bytes(body)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_body(body)
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    assert _get_tester().execute(f"PUT /v1/documents -b @{path}") == 0


def test_command_http_reports_missing_explicit_file(tmp_path):
    with pytest.raises(WrongParametersError, match="Cannot read request body"):
        _get_tester().execute(f"PUT /v1/documents -b @{tmp_path / 'missing.xml'}")


@pytest.mark.parametrize("prefix", ["", "@"])
def test_command_http_reports_unreadable_existing_file(tmp_path, mocker, prefix):
    path = tmp_path / "body.xml"
    path.write_text("<doc/>")
    mocker.patch.object(
        Path,
        "read_bytes",
        side_effect=PermissionError(errno.EACCES, "Permission denied"),
    )

    with pytest.raises(WrongParametersError, match="Permission denied"):
        _get_tester().execute(f"PUT /v1/documents -b {prefix}{path}")


@respx.mock
def test_command_http_post_without_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body("")
    ml_mocker.mock_post()

    tester = _get_tester()
    tester.execute("-e test POST /v1/documents")

    assert tester.command.option("body") is None


@respx.mock
def test_command_http_put_with_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("uri", "/doc.xml")
    ml_mocker.with_request_body(_BODY)
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    tester = _get_tester()
    tester.execute(f"-e test PUT /v1/documents uri=/doc.xml -b '{_BODY}'")

    assert tester.command.argument("method") == "PUT"
    assert tester.command.option("body") == _BODY


@respx.mock
def test_command_http_delete():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("uri", "/doc.xml")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    tester = _get_tester()
    tester.execute("-e test DELETE /v1/documents uri=/doc.xml")

    assert tester.command.argument("method") == "DELETE"
    assert tester.command.argument("params") == ["uri=/doc.xml"]


def test_command_http_rejects_malformed_param():
    tester = _get_tester()
    with pytest.raises(WrongParametersError) as err:
        tester.execute("-e test GET /manage/v2/hosts nonsense")

    expected_msg = "'nonsense' is neither a key=value param nor a key:value header!"
    assert err.value.args[0] == expected_msg


@pytest.mark.parametrize("token", ["=value", ":value"])
def test_command_http_rejects_empty_parameter_names(token):
    with pytest.raises(WrongParametersError, match="name cannot be empty"):
        _get_tester().execute(f"GET /v1/documents {token}")


@pytest.mark.parametrize("endpoint", ["http://example.com/", "/v1/documents#fragment"])
def test_command_http_rejects_non_endpoint_urls(endpoint):
    with pytest.raises(WrongParametersError, match="endpoint path"):
        _get_tester().execute(f"GET {endpoint}")


def _get_tester():
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find("http")
    return CommandTester(command)
