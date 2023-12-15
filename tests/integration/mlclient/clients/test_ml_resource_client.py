from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when
from requests import Response

from mlclient import MLResourceClient, MLResponseParser
from mlclient.calls import EvalCall

scenarios("ml_resource_client.feature")


@given(
    "I initialized an MLResourceClient's connection",
    target_fixture="client",
)
def init_client():
    client = MLResourceClient(auth_method="digest")
    client.connect()
    return client


@given(
    parsers.parse("I prepared the following {lang} code\n{code}"),
    target_fixture="call_config",
)
def prepare_code(lang, code):
    code = parse_step_input(code)
    return {lang: code}


@given(
    parsers.parse("I set the following variables\n{variables}"),
    target_fixture="call_config",
)
def set_variables(variables, call_config):
    variables = parse_step_input(variables)
    call_config["variables"] = variables[0]
    return call_config


@when("I call the EvalCall", target_fixture="response")
def call_eval(client, call_config):
    call = EvalCall(**call_config)
    return client.call(call)


@then(parsers.parse("I get a successful multipart response\n{expected_parts}"))
def verify_response(response: Response, expected_parts):
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
def close_client(client):
    client.disconnect()
    assert not client.is_connected()


def parse_step_input(
    step_input: str,
) -> str | list[dict]:
    lines = step_input.split("\n")
    delimiters_count = lines[0].count("|")
    is_table = delimiters_count > 0
    if not is_table:
        return step_input

    headings = [cell.strip() for cell in lines[0].split("|")][1:-1]
    rows = []
    for line in lines[1:]:
        if line.count("|") != delimiters_count:
            raise
        cells = [cell.strip() for cell in line.split("|")][1:-1]
        row = {}
        for i, heading in enumerate(headings):
            row[heading] = cells[i]
        rows.append(row)

    return rows
