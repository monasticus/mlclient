from __future__ import annotations

import pytest

from mlclient import MLClientManager, MLEnvironment
from mlclient.cli.connection import get_client
from mlclient.exceptions import NoSuchAppServerError, WrongParametersError


@pytest.mark.parametrize(
    ("selector", "port"), [(None, 8000), ("manage", 8002), ("8123", 8123)],
)
def test_connection_selects_identifier_or_port(selector, port, mocker):
    environment = MLEnvironment(
        **{
            "app-name": "test",
            "host": "localhost",
            "app-servers": [{"id": "rest", "port": 8000, "rest": True}],
        },
    )
    mocker.patch("mlclient.ml_environment.MLEnvironment.load", return_value=environment)
    client = get_client(MLClientManager("test"), selector)
    assert client.http.base_url == f"http://localhost:{port}"


@pytest.mark.parametrize("selector", ["0", "65536"])
def test_connection_rejects_invalid_port(selector):
    with pytest.raises(WrongParametersError, match="between 1 and 65535"):
        get_client(None, selector)


def test_connection_rejects_unknown_identifier(mocker):
    environment = MLEnvironment(**{"app-name": "test"})
    mocker.patch("mlclient.ml_environment.MLEnvironment.load", return_value=environment)
    with pytest.raises(NoSuchAppServerError):
        get_client(MLClientManager("test"), "missing")
