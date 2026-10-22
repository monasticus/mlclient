from __future__ import annotations

import re

import httpx
import pytest
import respx
from cleo.io.outputs.output import Verbosity
from cleo.testers.command_tester import CommandTester
from httpx import ConnectError

from mlclient import AsyncMLClient, MLClient
from mlclient.cli import MLCLIentApplication
from mlclient.cli.commands import health
from mlclient.env import MLEnvironment
from mlclient.exceptions import WrongParametersError
from mlclient.models import ClusterHealth
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
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)


@respx.mock
def test_command_health_reports_healthy():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 0
    output = tester.io.fetch_output()
    assert "HEALTHY" in output
    assert "UNHEALTHY" not in output


@respx.mock
def test_command_health_uses_health_config_without_a_rest_server(mocker):
    config = MLEnvironment(
        **{
            "app-servers": [
                {"id": "app-services", "rest": False},
                {"id": "health", "port": 9997, "auth": "app"},
            ],
        },
    )
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=config)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:9997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()
    tester = _get_tester()

    assert tester.execute("-e test") == 0
    assert route.call_count == 1
    assert "Authorization" not in route.calls.last.request.headers
    assert tester.io.fetch_output() == "HEALTHY\n"


@respx.mock
def test_command_health_reports_unhealthy_on_server_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

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
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(401)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    tester = _get_tester()
    with pytest.raises(httpx.HTTPStatusError):
        tester.execute("-e test")


@respx.mock
def test_command_health_ignores_watch_options_without_watch():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

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
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()
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
def test_command_health_watch_recovers_after_transport_and_server_errors(mocker):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()
    route.mock(
        side_effect=[
            httpx.Response(200),
            httpx.ConnectError("connection refused"),
            httpx.ReadTimeout("timed out"),
            httpx.Response(503),
            httpx.Response(200),
        ],
    )
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, None, None, KeyboardInterrupt],
    )
    tester = _get_tester()

    assert tester.execute("-e test --watch") == 0

    statuses = [line.split()[-1] for line in tester.io.fetch_output().splitlines()]
    assert statuses == ["HEALTHY", "UNREACHABLE", "UNREACHABLE", "UNHEALTHY", "HEALTHY"]
    assert route.call_count == 5


@respx.mock
def test_command_health_watch_uses_default_interval(mocker):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()
    sleep = mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=KeyboardInterrupt,
    )

    tester = _get_tester()
    tester.execute("-e test --watch")

    sleep.assert_called_once_with(5)


@respx.mock
def test_command_health_watch_accepts_minimum_interval(mocker):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()
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


@pytest.mark.parametrize("arguments", ["--no-ansi", ""])
@respx.mock
def test_command_health_watch_overwrite_appends_without_ansi(arguments, mocker):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, KeyboardInterrupt],
    )
    tester = _get_tester()

    assert (
        tester.execute(f"-e test --watch --overwrite {arguments}", decorated=False) == 0
    )

    output = tester.io.fetch_output()
    assert len(output.splitlines()) == 3
    assert "\x1b[" not in output


@respx.mock
def test_command_health_watch_overwrite_repaints_in_place(mocker):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, None, KeyboardInterrupt],
    )

    tester = _get_tester()
    status = tester.execute("-e test --watch --overwrite --lines 5", decorated=True)

    assert status == 0
    assert route.call_count == 4
    output = tester.io.fetch_output()
    assert "\x1b[1A" in output
    assert "HEALTHY" in output
    assert _TIMESTAMP.search(output)


@respx.mock
def test_command_health_watch_overwrite_keeps_only_last_lines(mocker):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, None, KeyboardInterrupt],
    )

    tester = _get_tester()
    tester.execute("-e test --watch --overwrite --lines 2", decorated=True)

    final_frame = tester.io.fetch_output().split("\x1b[2A")[-1]
    assert final_frame.count("HEALTHY") == 2


@respx.mock
def test_command_health_watch_overwrite_uses_default_lines(mocker):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(HEALTH_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, None, None, KeyboardInterrupt],
    )

    tester = _get_tester()
    tester.execute("-e test --watch --overwrite", decorated=True)

    final_frame = tester.io.fetch_output().split("\x1b[3A")[-1]
    assert final_frame.count("HEALTHY") == 3


@pytest.mark.parametrize("lines", ["0", "abc", "101", "99999999999999999999999999"])
def test_command_health_watch_rejects_invalid_lines(lines):
    tester = _get_tester()

    with pytest.raises(WrongParametersError):
        tester.execute(f"-e test --watch --overwrite --lines {lines}")


_CLUSTER = {"host-c": True, "host-a": True, "host-b": True}
_DEGRADED_CLUSTER = {"host-c": False, "host-a": True, "host-b": False}


def test_command_health_cluster_reports_healthy_host_count(mocker):
    _patch_cluster_health(mocker, ClusterHealth(healthy=True, hosts=_CLUSTER))
    tester = _get_tester()

    assert tester.execute("-e test --cluster") == 0
    assert tester.io.fetch_output() == "HEALTHY 3/3\n"


def test_command_health_cluster_lists_unhealthy_hosts_sorted_by_name(mocker):
    _patch_cluster_health(
        mocker,
        ClusterHealth(healthy=False, hosts=_DEGRADED_CLUSTER),
    )
    tester = _get_tester()

    assert tester.execute("-e test --cluster") == 1
    assert tester.io.fetch_output() == (
        "UNHEALTHY 1/3\n  UNHEALTHY  host-b\n  UNHEALTHY  host-c\n"
    )


def test_command_health_cluster_verbose_lists_every_host_sorted_by_name(mocker):
    _patch_cluster_health(
        mocker,
        ClusterHealth(healthy=False, hosts=_DEGRADED_CLUSTER),
    )
    tester = _get_tester()

    assert tester.execute("-e test --cluster", verbosity=Verbosity.VERBOSE) == 1
    assert tester.io.fetch_output() == (
        "UNHEALTHY 1/3\n  HEALTHY    host-a\n  UNHEALTHY  host-b\n  UNHEALTHY  host-c\n"
    )


def test_command_health_cluster_sorts_numbers_in_host_names_by_value(mocker):
    hosts = {"ip-10-0-0-121": False, "ip-10-0-0-5": False, "ip-10-0-0-34": False}
    _patch_cluster_health(mocker, ClusterHealth(healthy=False, hosts=hosts))
    tester = _get_tester()

    tester.execute("-e test --cluster")

    assert tester.io.fetch_output().splitlines()[1:] == [
        "  UNHEALTHY  ip-10-0-0-5",
        "  UNHEALTHY  ip-10-0-0-34",
        "  UNHEALTHY  ip-10-0-0-121",
    ]


def test_command_health_cluster_verbose_lists_hosts_of_a_healthy_cluster(mocker):
    _patch_cluster_health(mocker, ClusterHealth(healthy=True, hosts=_CLUSTER))
    tester = _get_tester()

    assert tester.execute("-e test --cluster", verbosity=Verbosity.VERBOSE) == 0
    assert tester.io.fetch_output() == (
        "HEALTHY 3/3\n  HEALTHY    host-a\n  HEALTHY    host-b\n  HEALTHY    host-c\n"
    )


@pytest.mark.parametrize(
    ("healthy", "expected_status", "expected_output"),
    [
        (True, 0, "HEALTHY (overall)\n"),
        (False, 1, "UNHEALTHY (overall)\n"),
    ],
)
def test_command_health_cluster_without_host_breakdown_reports_overall(
    mocker,
    healthy,
    expected_status,
    expected_output,
):
    _patch_cluster_health(mocker, ClusterHealth(healthy=healthy, hosts=None))
    tester = _get_tester()

    assert (
        tester.execute("-e test --cluster", verbosity=Verbosity.VERBOSE)
        == expected_status
    )
    assert tester.io.fetch_output() == expected_output


def test_command_health_cluster_colours_host_count_apart_from_status(mocker):
    _patch_cluster_health(mocker, ClusterHealth(healthy=True, hosts=_CLUSTER))
    tester = _get_tester()

    tester.execute("-e test --cluster", decorated=True)

    output = tester.io.fetch_output()
    assert "\x1b[32;1mHEALTHY\x1b[39;22m" in output
    assert "\x1b[36m3/3\x1b[39m" in output


def test_command_health_cluster_does_not_probe_the_healthcheck_server(mocker):
    _patch_cluster_health(mocker, ClusterHealth(healthy=True, hosts=_CLUSTER))
    healthcheck = mocker.patch.object(MLClient, "healthcheck")
    tester = _get_tester()

    tester.execute("-e test --cluster")

    healthcheck.assert_not_called()


def test_command_health_cluster_watch_names_unhealthy_hosts(mocker):
    _patch_cluster_health(
        mocker,
        side_effect=[
            ClusterHealth(healthy=True, hosts=_CLUSTER),
            ClusterHealth(healthy=False, hosts=_DEGRADED_CLUSTER),
            httpx.ConnectError("connection refused"),
            ClusterHealth(healthy=True, hosts=None),
        ],
    )
    mocker.patch(
        "mlclient.cli.commands.health.time.sleep",
        side_effect=[None, None, None, KeyboardInterrupt],
    )
    tester = _get_tester()

    assert tester.execute("-e test --cluster --watch") == 0

    lines = [
        _TIMESTAMP.sub("<time>", line) for line in tester.io.fetch_output().splitlines()
    ]
    assert lines == [
        "<time> HEALTHY 3/3",
        "<time> UNHEALTHY 1/3 down: host-b, host-c",
        "<time> UNREACHABLE",
        "<time> HEALTHY (overall)",
    ]


def test_command_health_cluster_in_several_environments_shows_host_counts(mocker):
    _patch_async_cluster_health(mocker, ClusterHealth(healthy=True, hosts=_CLUSTER))
    tester = _get_tester()

    assert tester.execute("-e test -e other --cluster") == 0

    body = tester.io.fetch_output().splitlines()[3]
    assert body.count("HEALTHY 3/3") == 2
    assert "host-a" not in tester.io.fetch_output()


def test_command_health_cluster_in_several_environments_fails_when_one_is_unhealthy(
    mocker,
):
    _patch_async_cluster_health(
        mocker,
        ClusterHealth(healthy=False, hosts=_DEGRADED_CLUSTER),
    )
    tester = _get_tester()

    assert (
        tester.execute("-e test -e other --cluster", verbosity=Verbosity.VERBOSE) == 1
    )

    output = tester.io.fetch_output()
    assert output.count("UNHEALTHY 1/3") == 2
    assert "host-b" not in output


def test_command_health_cluster_in_several_environments_colours_host_count(mocker):
    _patch_async_cluster_health(mocker, ClusterHealth(healthy=True, hosts=_CLUSTER))
    tester = _get_tester()

    tester.execute("-e test -e other --cluster", decorated=True)

    assert "\x1b[36m3/3\x1b[39m" in tester.io.fetch_output()


def test_command_health_cluster_watch_in_several_environments_adds_rows(mocker):
    _patch_async_cluster_health(
        mocker,
        side_effect=[
            ClusterHealth(healthy=True, hosts=_CLUSTER),
            ClusterHealth(healthy=True, hosts=_CLUSTER),
            ClusterHealth(healthy=False, hosts=None),
            ClusterHealth(healthy=False, hosts=None),
        ],
    )
    mocker.patch(
        "mlclient.cli.commands.health.asyncio.sleep",
        side_effect=[None, KeyboardInterrupt],
    )
    tester = _get_tester()

    assert tester.execute("-e test -e other --cluster --watch") == 0

    rows = [
        line
        for line in tester.io.fetch_output().splitlines()
        if _TIMESTAMP.search(line)
    ]
    assert len(rows) == 2
    assert rows[0].count("HEALTHY 3/3") == 2
    assert rows[1].count("UNHEALTHY (overall)") == 2


def _patch_cluster_health(mocker, health=None, side_effect=None):
    return mocker.patch.object(
        MLClient,
        "cluster_healthcheck",
        return_value=health,
        side_effect=side_effect,
    )


def _patch_async_cluster_health(mocker, health=None, side_effect=None):
    return mocker.patch.object(
        AsyncMLClient,
        "cluster_healthcheck",
        return_value=health,
        side_effect=side_effect,
    )


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    command = app.find("health")
    return CommandTester(command)


@pytest.mark.parametrize("overwrite", [False, True])
@pytest.mark.parametrize("decorated", [False, True])
@respx.mock
def test_command_health_multi_environment_watch_retains_only_repainted_rows(
    mocker,
    overwrite,
    decorated,
):
    respx.head(HEALTH_URL).respond(200)
    mocker.patch.object(health.asyncio, "sleep", side_effect=[None, KeyboardInterrupt])
    retained_rows = []
    finish = health._WatchTable.finish

    def record_history(table, started_at, runs):
        finish(table, started_at, runs)
        retained_rows.append(len(table._finished_rows))

    mocker.patch.object(health._WatchTable, "finish", record_history)
    tester = _get_tester()
    options = " --overwrite --lines 2" if overwrite else ""

    assert (
        tester.execute(
            f"-e first -e second --watch{options}",
            decorated=decorated,
        )
        == 0
    )
    assert retained_rows == ([1, 1] if overwrite and decorated else [0, 0])
    output = tester.io.fetch_output()
    assert "first" in output
    assert "second" in output
    assert "HEALTHY" in output


@pytest.mark.parametrize("status_code", [200, 503])
@respx.mock
def test_command_health_multi_environment_reports_each_verdict(status_code):
    respx.head(HEALTH_URL).respond(status_code)
    tester = _get_tester()

    assert tester.execute("-e first -e second") == (0 if status_code == 200 else 1)
    status = "HEALTHY" if status_code == 200 else "UNHEALTHY"
    assert tester.io.fetch_output().count(status) == 2


@respx.mock
def test_command_health_multi_environment_reports_unreachable():
    respx.head(HEALTH_URL).mock(side_effect=ConnectError("server unreachable"))
    tester = _get_tester()

    assert tester.execute("-e first -e second") == 1
    assert tester.io.fetch_output().count("UNREACHABLE") == 2


@respx.mock
def test_command_health_multi_environment_escapes_configuration_error(mocker):
    mocker.patch(
        "mlclient.env.MLEnvironment.load",
        side_effect=WrongParametersError("Missing environment <info>demo</info>"),
    )
    tester = _get_tester()

    assert tester.execute("-e first -e second") == 1
    assert tester.io.fetch_output().count("<info>demo</info>") == 2
    assert not respx.calls
