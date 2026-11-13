from __future__ import annotations

import asyncio
import errno
import os
from pathlib import Path

import pytest
import respx
from cleo.testers.command_tester import CommandTester
from httpx import Response

from mlclient.cli import MLCLIentApplication
from mlclient.env import MLEnvironment
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
    target = "mlclient.env.MLEnvironment.load"
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
    assert tester.command.option("environment") == ["test"]
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
    assert (
        tester.execute(
            "GET /v1/documents?uri=/one.xml "
            "uri=/two.xml uri=/three.xml category=content",
        )
        == 0
    )


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
def test_command_http_error_with_body_prints_body_and_exits_with_1():
    respx.get("http://localhost:8002/v1/documents").respond(
        404,
        text='{"errorResponse": {"messageCode": "RESTAPI-NODOCUMENT"}}',
    )

    tester = _get_tester()
    assert tester.execute("GET /v1/documents uri=/missing.json") == 1
    assert tester.io.fetch_output() == (
        '{"errorResponse": {"messageCode": "RESTAPI-NODOCUMENT"}}\n'
    )
    assert tester.io.fetch_error() == ""


@respx.mock
def test_command_http_error_without_body_reports_status_line_on_stderr():
    respx.get("http://localhost:8002/v1/ping").respond(404)

    tester = _get_tester()
    assert tester.execute("GET /v1/ping") == 1
    assert tester.io.fetch_output() == ""
    assert tester.io.fetch_error() == (
        "HTTP 404 Not Found for http://localhost:8002/v1/ping\n"
    )


@respx.mock
def test_command_http_include_flag_prints_error_response_only():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/nope")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body('{"errorResponse": {}}')
    ml_mocker.mock_get()

    tester = _get_tester()
    assert tester.execute("-e test -i GET /manage/v2/nope") == 1

    command_output = tester.io.fetch_output()
    assert command_output.startswith("HTTP/1.1 404 Not Found\n")
    assert '{"errorResponse": {}}' in command_output
    assert tester.io.fetch_error() == ""


@pytest.mark.parametrize("options", ["-i GET", "HEAD"])
@respx.mock
def test_command_http_error_without_body_keeps_status_line_of_protocol_output(
    options,
):
    respx.route(url="http://localhost:8002/v1/ping").respond(401)

    tester = _get_tester()
    assert tester.execute(f"{options} /v1/ping") == 1
    assert tester.io.fetch_output().startswith("HTTP/1.1 401 Unauthorized\n")
    assert tester.io.fetch_error() == ""


@pytest.mark.parametrize(
    "content_type", ["application/json", "text/plain; charset=UTF-8", None],
)
@pytest.mark.parametrize("pretty_option", ["--pretty", "-p"])
@respx.mock
def test_command_http_pretty_formats_response_body(pretty_option, content_type):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/hosts")
    ml_mocker.with_response_code(200)
    if content_type is not None:
        ml_mocker.with_response_header("Content-Type", content_type)
    ml_mocker.with_response_body('{"a": {"b": 1}}')
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute(f"-e test {pretty_option} GET /manage/v2/hosts")

    assert tester.io.fetch_output() == '{\n  "a": {\n    "b": 1\n  }\n}\n'


@respx.mock
def test_command_http_preserves_json_body_by_default():
    body = '{"key":"zażółć"}'
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("uri", "/doc.json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(body)
    ml_mocker.mock_get()

    tester = _get_tester()
    assert tester.execute("GET /v1/documents uri=/doc.json") == 0
    assert tester.io.fetch_output() == body + "\n"


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
    assert (
        tester.execute(
            f"POST /v1/documents {header}:application/json -b '{body}'",
        )
        == 0
    )


@pytest.mark.parametrize("stat_fails", [False, True])
@respx.mock
def test_command_http_accepts_body_longer_than_a_file_name(monkeypatch, stat_fails):
    if stat_fails:

        def fail_stat(_self):
            raise OSError(errno.ENAMETOOLONG, "File name too long")

        monkeypatch.setattr(Path, "is_file", fail_stat)
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


@pytest.mark.parametrize("prefix", ["", "@"])
@respx.mock
def test_command_http_sets_content_type_from_body_file_extension(tmp_path, prefix):
    path = tmp_path / "doc.json"
    path.write_text('{"hello": "world"}')
    route = respx.put("http://localhost:8002/v1/documents").respond(201)

    assert (
        _get_tester().execute(f"PUT /v1/documents uri=/doc.json -b {prefix}{path}") == 0
    )
    request = route.calls.last.request
    assert request.headers["Content-Type"] == "application/json"
    assert request.content == b'{"hello": "world"}'


@pytest.mark.parametrize("header", ["Content-Type", "content-type"])
@respx.mock
def test_command_http_explicit_content_type_wins_over_body_file_extension(
    tmp_path,
    header,
):
    path = tmp_path / "doc.json"
    path.write_text("{}")
    route = respx.put("http://localhost:8002/v1/documents").respond(201)

    assert (
        _get_tester().execute(f"PUT /v1/documents {header}:text/plain -b @{path}") == 0
    )
    assert route.calls.last.request.headers.get_list("Content-Type") == ["text/plain"]


@pytest.mark.parametrize("file_name", ["body.unknown-extension", "body"])
@respx.mock
def test_command_http_sends_no_content_type_for_unknown_body_file_extension(
    tmp_path,
    file_name,
):
    path = tmp_path / file_name
    path.write_text("payload")
    route = respx.put("http://localhost:8002/v1/documents").respond(201)

    assert _get_tester().execute(f"PUT /v1/documents -b @{path}") == 0
    assert "Content-Type" not in route.calls.last.request.headers


@respx.mock
def test_command_http_sends_no_content_type_for_literal_body():
    route = respx.put("http://localhost:8002/v1/documents").respond(201)

    assert _get_tester().execute("PUT /v1/documents -b '{\"a\":1}'") == 0
    request = route.calls.last.request
    assert "Content-Type" not in request.headers
    assert request.content == b'{"a":1}'


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


@pytest.mark.parametrize(
    ("token", "name", "value"),
    [
        ("rs:view=versions", "rs:view", "versions"),
        ("trans:name=value", "trans:name", "value"),
        ("perm:rest-reader=read", "perm:rest-reader", "read"),
        ("prop:status=draft", "prop:status", "draft"),
        ("value:id=12", "value:id", "12"),
        ("bind:limit:xs:integer=5", "bind:limit:xs:integer", "5"),
        ("bind:label@en=hello", "bind:label@en", "hello"),
        ("get:uri=xs:string", "get:uri", "xs:string"),
        ("put:uri=xs:string", "put:uri", "xs:string"),
        ("post:uri=xs:string", "post:uri", "xs:string"),
        ("delete:uri=xs:string", "delete:uri", "xs:string"),
    ],
)
@respx.mock
def test_command_http_sends_known_prefixed_tokens_as_query_params(token, name, value):
    route = respx.get("http://localhost:8002/v1/documents").respond(200)

    assert _get_tester().execute(f"GET /v1/documents {token}") == 0
    request = route.calls.last.request
    assert request.url.params.get_list(name) == [value]
    assert name.split(":", 1)[0] not in request.headers


@pytest.mark.parametrize(
    ("token", "name", "value"),
    [
        ("rs:value", "rs", "value"),
        (
            "Content-Type:multipart/mixed; boundary=xyz",
            "content-type",
            "multipart/mixed; boundary=xyz",
        ),
        ("X-Trace:rs:view=versions", "x-trace", "rs:view=versions"),
    ],
)
@respx.mock
def test_command_http_sends_other_colon_tokens_as_headers(token, name, value):
    route = respx.get("http://localhost:8002/v1/documents").respond(200)

    assert _get_tester().execute(f"GET /v1/documents '{token}'") == 0
    request = route.calls.last.request
    assert request.headers[name] == value
    assert not request.url.params


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


@respx.mock
def test_command_http_multi_environment_records_formatting_failure(mocker):
    route = respx.get("http://localhost:8002/manage/v2/hosts").respond(200)
    tester = _get_tester()
    mocker.patch.object(
        tester.command,
        "_render",
        side_effect=[ValueError("Cannot format response"), "peer response"],
    )

    assert tester.execute("-e first -e second GET /manage/v2/hosts") == 1
    output = tester.io.fetch_output()
    assert "Cannot format response" in output
    assert "peer response" in output
    assert route.call_count == 2


@respx.mock
def test_command_http_multi_environment_deduplicates_and_preserves_literal_output():
    route = respx.get("http://localhost:8002/manage/v2/hosts").respond(
        200,
        text="<info>literal</info>",
    )
    tester = _get_tester()

    assert tester.execute("-e first -e second -e first GET /manage/v2/hosts") == 0
    output = tester.io.fetch_output()
    assert output.count("<info>literal</info>") == 2
    assert "first" in output
    assert "second" in output
    assert route.call_count == 2


@respx.mock
def test_command_http_multi_environment_reports_http_errors_on_numeric_connection():
    route = respx.get("http://localhost:8100/manage/v2/hosts").respond(
        400,
        text="temporarily unavailable",
    )
    tester = _get_tester()

    assert tester.execute("-e first -e second -c 8100 GET /manage/v2/hosts") == 1
    assert tester.io.fetch_output().count("temporarily unavailable") == 2
    assert route.call_count == 2


@respx.mock
def test_command_http_multi_environment_keeps_full_final_output(mocker):
    mocker.patch(
        "mlclient.cli.commands._multi_env_common.shutil.get_terminal_size",
        return_value=os.terminal_size((120, 12)),
    )
    delays = iter([0, 0.15])
    body = "\n".join([*(f"line {index}" for index in range(20)), "final line"])

    async def respond(_request):
        await asyncio.sleep(next(delays))
        return Response(200, text=body)

    respx.get("http://localhost:8002/manage/v2/hosts").mock(side_effect=respond)
    tester = _get_tester()

    assert (
        tester.execute(
            "-e first -e second GET /manage/v2/hosts",
            decorated=True,
        )
        == 0
    )
    output = tester.io.fetch_output()
    assert "more lines" in output
    assert "final line" in output


@pytest.mark.parametrize("content_type", ["text/plain; charset=UTF-8", None])
@respx.mock
def test_command_http_multi_environment_pretty_detects_json_payload(content_type):
    headers = {"Content-Type": content_type} if content_type is not None else {}
    route = respx.get("http://localhost:8002/v1/config/query").respond(
        200,
        headers=headers,
        content=b'[{"name":"orders"}]',
    )
    tester = _get_tester()

    assert tester.execute("get /v1/config/query -e dev -e qa --pretty") == 0
    output = tester.io.fetch_output()
    assert output.count('    "name": "orders"') == 2
    assert '[{"name":"orders"}]' not in output
    assert route.call_count == 2


@respx.mock
def test_command_http_multi_environment_shows_status_line_for_empty_error_body():
    respx.get("http://localhost:8002/v1/ping").respond(404)
    tester = _get_tester()

    assert tester.execute("-e first -e second GET /v1/ping") == 1
    output = tester.io.fetch_output()
    assert output.count("HTTP 404 Not Found for") == 2
