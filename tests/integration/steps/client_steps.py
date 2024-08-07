from __future__ import annotations

import datetime

from pytest_bdd import given, parsers, then, when
from requests import Response

from mlclient import MLResourceClient, MLResourcesClient
from mlclient.calls import EvalCall

from .common import parse_step_input


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
        msg = (
            f"Incorrect client type! "
            f"Expected: [MLResourceClient, MLResourcesClient], got: [{client_type}]"
        )
        raise ValueError(msg)
    client.connect()
    return client


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
    client: MLResourceClient,
    call_config: dict,
) -> Response:
    call = EvalCall(**call_config)
    return client.call(call)


@when("I evaluate the code", target_fixture="response")
def eval_(
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
            params[time_param] = params[time_param].replace(
                "<today>",
                str(datetime.date.today()),
            )
    params["filename"] = (f"{client.port}_{logs_type.capitalize()}Log.txt",)
    params["data_format"] = "json"
    return client.get_logs(**params)


@then("I close the connection")
def close_client(
    client: MLResourceClient,
):
    client.disconnect()
    assert not client.is_connected()
