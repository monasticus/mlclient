from __future__ import annotations

import datetime

from pytest_bdd import given, parsers, then, when
from requests import Response
from time import sleep

from mlclient import MLResourceClient, MLResourcesClient, MLResponseParser
from mlclient.calls import EvalCall

INPUT_DELIMITER = "|"


@given(
    parsers.parse("I initialized an {client_type}'s connection"),
    target_fixture="client",
)
def init_client(
    client_type: str,
) -> MLResourceClient:
    if client_type == "MLResourceClient":
        client = MLResourceClient(auth_method="digest")
    elif client_type == "MLResourcesClient":
        client = MLResourcesClient(auth_method="digest")
    else:
        raise
    client.connect()
    return client


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
) -> int:
    count = int(count)
    with MLResourcesClient(auth_method="digest") as client:
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


@when("I call the EvalCall", target_fixture="response")
def call_eval(
    client: MLResourceClient,
    call_config: dict,
) -> Response:
    call = EvalCall(**call_config)
    return client.call(call)


@when("I evaluate the code", target_fixture="response")
def eval_code(
    client: MLResourcesClient,
    call_config: dict,
) -> Response:
    return client.eval(**call_config)


@when(
    parsers.parse("I get {logs_type} logs\n{params}"),
    target_fixture="response",
)
def get_logs(
    client: MLResourcesClient,
    logs_type: str,
    params: str,
) -> Response:
    params = parse_step_input(params)[0]
    for time_param in ["start_time", "end_time"]:
        if time_param in params:
            params[time_param] = params[time_param].replace("<today>", str(datetime.date.today()))
    params["filename"] = f"{client.port}_{logs_type.capitalize()}Log.txt",
    params["data_format"] = "json"
    return client.get_logs(**params)


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


@then("I close the connection")
def close_client(
    client: MLResourceClient,
):
    client.disconnect()
    assert not client.is_connected()


def parse_step_input(
    step_input: str,
) -> str | list[dict]:
    lines = step_input.split("\n")
    delimiters_count = lines[0].count(INPUT_DELIMITER)
    is_table = delimiters_count > 0
    if not is_table:
        return step_input

    return _parse_step_input_table(lines, delimiters_count)


def _parse_step_input_table(
    input_lines: list[str],
    delimiters_count: int,
) -> list[dict]:
    headings = [cell.strip() for cell in input_lines[0].split(INPUT_DELIMITER)][1:-1]
    rows = []
    for line in input_lines[1:]:
        if line.count(INPUT_DELIMITER) != delimiters_count:
            raise
        cells = [cell.strip() for cell in line.split(INPUT_DELIMITER)][1:-1]
        row = {heading: cells[i] for i, heading in enumerate(headings)}
        rows.append(row)

    return rows


__all__ = [
    # given
    "init_client",
    "prepare_code",
    "set_variables",
    # when
    "call_eval",
    "eval_code",
    # then
    "verify_response",
    "verify_multipart_response",
    "close_client",
]
