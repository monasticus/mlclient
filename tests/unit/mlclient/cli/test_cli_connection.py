from __future__ import annotations

import pytest

from mlclient import MLClientManager
from mlclient.cli.connection import get_async_client, get_client
from mlclient.env import MLEnvironment
from mlclient.exceptions import NoSuchAppServerError, WrongParametersError


@pytest.mark.parametrize(
    ("selector", "port"),
    [(None, 8000), ("manage", 8002), ("8123", 8123)],
)
def test_connection_selects_identifier_or_port(selector, port, mocker):
    environment = MLEnvironment(
        **{
            "app-name": "test",
            "host": "localhost",
            "app-servers": [{"id": "rest", "port": 8000, "rest": True}],
        },
    )
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=environment)
    client = get_client(MLClientManager("test"), selector)
    assert client.http.base_url == f"http://localhost:{port}"


@pytest.mark.parametrize("selector", ["0", "65536"])
def test_connection_rejects_invalid_port(selector):
    with pytest.raises(WrongParametersError, match="between 1 and 65535"):
        get_client(None, selector)


@pytest.mark.parametrize("create_client", [get_client, get_async_client])
def test_connection_rejects_unknown_identifier(create_client, mocker):
    environment = MLEnvironment(
        **{"app-servers": [{"id": "rest", "port": 8010, "rest": True}]},
    )
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=environment)
    with pytest.raises(NoSuchAppServerError) as err:
        create_client(MLClientManager("staging"), "restt")
    assert str(err.value) == (
        "There's no [restt] app server configuration in the [staging] environment. "
        "Available: rest (8010), app-services (8000), manage (8002), admin (8001), "
        "health (7997).\n"
        "Pass a configured id or a port number to -c, e.g. -c 8010."
    )
    assert err.value.__cause__ is None
