from __future__ import annotations

import datetime

from httpx import Response
from pytest_bdd import given, parsers, then, when

from mlclient import MLClient
from mlclient.calls import EvalCall

from .common import parse_step_input


@given("I connected to MarkLogic", target_fixture="ml")
def init_ml() -> MLClient:
    ml = MLClient(auth_method="digest")
    ml.connect()
    return ml


@given(
    parsers.parse("I prepared the following {lang} code to eval\n{code}"),
    target_fixture="call_config",
)
def prepare_code(
    lang: str,
    code: str,
) -> dict:
    code = parse_step_input(code)
    return {lang: code}


@given(
    parsers.parse("I set the following variables for the code\n{variables}"),
    target_fixture="call_config",
)
def set_variables(
    variables: str,
    call_config: dict,
) -> dict:
    variables = parse_step_input(variables)
    call_config["variables"] = variables[0]
    return call_config


@when("I call the EvalCall", target_fixture="response")
def call_eval(
    ml: MLClient,
    call_config: dict,
) -> Response:
    call = EvalCall(**call_config)
    return ml.rest.call(call)


@when("I evaluate the code", target_fixture="response")
def eval_(
    ml: MLClient,
    call_config: dict,
) -> Response:
    return ml.rest.eval.post(**call_config)


@when(
    parsers.parse("I get {logs_type} logs\n{params}"),
    target_fixture="response",
)
def get_logs(
    ml: MLClient,
    logs_type: str,
    params: str,
) -> Response:
    params = parse_step_input(params)[0]
    for time_param in ["start_time", "end_time"]:
        if time_param in params:
            params[time_param] = params[time_param].replace(
                "<today>",
                str(datetime.date.today()),
            )
    params["filename"] = (f"{ml.http.port}_{logs_type.capitalize()}Log.txt",)
    params["data_format"] = "json"
    return ml.manage.logs.get(**params)


@then("I close the connection")
def close_ml(
    ml: MLClient,
):
    ml.disconnect()
    assert not ml.is_connected()
