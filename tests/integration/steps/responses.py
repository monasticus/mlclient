from __future__ import annotations

from pytest_bdd import parsers, then
from requests import Response

from mlclient import MLResponseParser

from .common import parse_step_input


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
