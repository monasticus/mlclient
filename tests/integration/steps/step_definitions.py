from __future__ import annotations

from time import sleep

from pytest_bdd import given, parsers, then
from requests import Response

from mlclient import MLResourcesClient, MLResponseParser

from .common import parse_step_input


@given(
    parsers.parse("I prepared the following {lang} code\n{code}"),
    target_fixture="call_config",
)
def prepare_code(
    lang: str,
    code: str,
) -> dict:
    code = parse_step_input(code)
    return {lang: code}


@given(
    parsers.parse("I set the following variables\n{variables}"),
    target_fixture="call_config",
)
def set_variables(
    variables: str,
    call_config: dict,
) -> dict:
    variables = parse_step_input(variables)
    call_config["variables"] = variables[0]
    return call_config


@given(
    parsers.parse("I produce {count} test logs\n{pattern}"),
    target_fixture="test_logs_count",
)
def produce_logs(
    count: str,
    pattern: str,
    client: MLResourcesClient,
) -> int:
    count = int(count)
    for i in range(1, count + 1):
        log = pattern.replace("<i>", str(i))
        client.eval(xquery=f'xdmp:log("{log}", "error")')
    return count


@given(
    parsers.parse("I wait {seconds} second(s)"),
)
def wait(
    seconds: str,
):
    sleep(int(seconds))


@then(parsers.parse("I get a successful response"))
def verify_response(
    response: Response,
):
    assert response.status_code == 200
    assert response.reason == "OK"


@then(parsers.parse("I get a successful multipart response\n{expected_parts}"))
def verify_multipart_response(
    response: Response,
    expected_parts: str,
):
    expected_parts = parse_step_input(expected_parts)

    parsed_resp = MLResponseParser.parse(response, str)
    assert response.status_code == 200
    if len(expected_parts) == 1:
        assert parsed_resp == expected_parts[0]["text"]
    else:
        assert len(expected_parts) == len(parsed_resp)
        for i, expected_part in enumerate(expected_parts):
            assert parsed_resp[i] == expected_part["text"]


@then("I find produced logs")
def verify_produced_logs(
    test_logs_count: int,
    response: Response,
):
    logfile = response.json()["logfile"]
    logs_count = len(logfile["log"])
    assert logs_count % test_logs_count == 0


@then("I find requests producing logs")
def verify_requests_producing_logs(
    test_logs_count: int,
    response: Response,
):
    logfile = response.json()["logfile"]

    logs = logfile["message"].split("\n")
    eval_logs = [
        log
        for log in logs
        if '"POST /v1/eval HTTP/1.1"' in log and "python-requests" in log
    ]
    assert len(eval_logs) >= test_logs_count


@then(parsers.parse("I confirm returned {logs_type} logs structure"))
def verify_logs_structure(
    logs_type: str,
    response: Response,
):
    logfile = response.json()["logfile"]
    if logs_type in ["request", "access"]:
        assert "log" not in logfile
        assert isinstance(logfile.get("message"), str) or len(logfile) == 6
    elif logs_type == "error":
        assert "message" not in logfile
        assert isinstance(logfile.get("log"), list) or len(logfile) == 6
