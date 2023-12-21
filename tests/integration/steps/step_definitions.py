from __future__ import annotations

from time import sleep

from pytest_bdd import given, parsers

from mlclient import MLResourcesClient

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
