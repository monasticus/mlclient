from __future__ import annotations

import re

import httpx
import pytest
import respx
from cleo.testers.command_tester import CommandTester

from mlclient import MLClient, MLEnvironment
from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import WrongParametersError
from tests.utils.ml_mockers import MLRespXMocker

HEALTH_URL = "http://localhost:7997/"
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


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
        ],
    }
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config):
    mocker.patch("mlclient.ml_environment.MLEnvironment.load", return_value=ml_config)


@respx.mock
def test_command_health_reports_healthy():
    _mock_healthcheck_response(200)

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 0
    output = tester.io.fetch_output()
    assert "HEALTHY" in output
    assert "UNHEALTHY" not in output


@respx.mock
def test_command_health_reports_unhealthy_on_server_error():
    _mock_healthcheck_response(503)

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 1
    assert "UNHEALTHY" in tester.io.fetch_output()


def test_command_health_propagates_connection_error(mocker):
    mocker.patch.object(
        MLClient,
        "healthcheck",
        side_effect=httpx.ConnectError("connection refused"),
    )

    tester = _get_tester()
    with pytest.raises(httpx.ConnectError):
        tester.execute("-e test")


@respx.mock
def test_command_health_propagates_client_error():
    _mock_healthcheck_response(401)

    tester = _get_tester()
    with pytest.raises(httpx.HTTPStatusError):
        tester.execute("-e test")


@respx.mock
def test_command_health_ignores_watch_options_without_watch():
    route = _mock_healthcheck_response(200)

    tester = _get_tester()
    status = tester.execute("-e test --overwrite --lines 5 --interval 9")

    assert status == 0
    assert route.call_count == 1
    output = tester.io.fetch_output()
    assert "HEALTHY" in output
    assert not _TIMESTAMP.search(output)
    assert "\x1b[" not in output


@respx.mock
def test_command_health_watch_appends_until_interrupted(mocker):
    route = _mock_healthcheck_response(200)
    sleep = mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, KeyboardInterrupt],
    )

    tester = _get_tester()
    status = tester.execute("-e test --watch --interval 2")

    assert status == 0
    assert route.call_count == 3
    sleep.assert_called_with(2)
    output = tester.io.fetch_output()
    assert output.count("HEALTHY") == 3
    assert _TIMESTAMP.search(output)
    assert "\x1b[" not in output


@respx.mock
def test_command_health_watch_uses_default_interval(mocker):
    _mock_healthcheck_response(200)
    sleep = mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=KeyboardInterrupt,
    )

    tester = _get_tester()
    tester.execute("-e test --watch")

    sleep.assert_called_once_with(5)


@respx.mock
def test_command_health_watch_accepts_minimum_interval(mocker):
    _mock_healthcheck_response(200)
    sleep = mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=KeyboardInterrupt,
    )

    tester = _get_tester()
    tester.execute("-e test --watch --interval 1")

    sleep.assert_called_once_with(1)


@pytest.mark.parametrize("interval", ["0", "abc", "99999999999999999999999999"])
def test_command_health_watch_rejects_invalid_interval(interval):
    tester = _get_tester()

    with pytest.raises(WrongParametersError):
        tester.execute(f"-e test --watch --interval {interval}")


@respx.mock
def test_command_health_watch_overwrite_repaints_in_place(mocker):
    route = _mock_healthcheck_response(200)
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, None, KeyboardInterrupt],
    )

    tester = _get_tester()
    status = tester.execute("-e test --watch --overwrite --lines 5")

    assert status == 0
    assert route.call_count == 4
    output = tester.io.fetch_output()
    assert "\x1b[1A" in output
    assert "HEALTHY" in output
    assert _TIMESTAMP.search(output)


@respx.mock
def test_command_health_watch_overwrite_keeps_only_last_lines(mocker):
    _mock_healthcheck_response(200)
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, None, KeyboardInterrupt],
    )

    tester = _get_tester()
    tester.execute("-e test --watch --overwrite --lines 2")

    final_frame = tester.io.fetch_output().split("\x1b[2A")[-1]
    assert final_frame.count("HEALTHY") == 2


@respx.mock
def test_command_health_watch_overwrite_uses_default_lines(mocker):
    _mock_healthcheck_response(200)
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, None, None, KeyboardInterrupt],
    )

    tester = _get_tester()
    tester.execute("-e test --watch --overwrite")

    final_frame = tester.io.fetch_output().split("\x1b[3A")[-1]
    assert final_frame.count("HEALTHY") == 3


@pytest.mark.parametrize("lines", ["0", "abc", "101", "99999999999999999999999999"])
def test_command_health_watch_rejects_invalid_lines(lines):
    tester = _get_tester()

    with pytest.raises(WrongParametersError):
        tester.execute(f"-e test --watch --overwrite --lines {lines}")


def _mock_healthcheck_response(status_code: int):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(status_code)
    ml_mocker.with_empty_response_body()
    return ml_mocker.mock_head()


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    command = app.find("health")
    return CommandTester(command)
