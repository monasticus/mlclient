from __future__ import annotations

import pytest
from cleo.testers.command_tester import CommandTester
from pytest_mock import MockerFixture

from mlclient.cli import MLCLIentApplication
from mlclient.env import MLEnvironment
from mlclient.exceptions import NoSuchAppServerError, WrongParametersError


@pytest.fixture(autouse=True)
def ml_config() -> MLEnvironment:
    config = {
        "host": "ml.example.com",
        "protocol": "https",
        "app-servers": [
            {"id": "content", "port": 8100},
        ],
    }
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def _setup(mocker: MockerFixture, ml_config: MLEnvironment) -> None:
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)


@pytest.fixture
def clipboard_process(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("mlclient.cli.clipboard.sys.platform", "linux")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    return mocker.patch("mlclient.cli.clipboard.subprocess.run")


@pytest.fixture
def browser_open(mocker: MockerFixture):
    return mocker.patch("mlclient.cli.commands.url.webbrowser.open")


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("url"))


# --- no target: the three basic URLs ---


def test_no_target_prints_the_three_basic_urls():
    tester = _get_tester()
    status = tester.execute("")

    assert status == 0
    output = tester.io.fetch_output()
    assert "QConsole" in output
    assert "https://ml.example.com:8000/qconsole" in output
    assert "Admin UI" in output
    assert "https://ml.example.com:8001" in output
    assert "Monitoring Dashboard" in output
    assert "https://ml.example.com:8002/dashboard" in output


def test_no_target_defaults_to_local_environment():
    tester = _get_tester()
    tester.execute("")

    assert tester.command.option("environment") == "local"


def test_no_target_with_open_is_rejected():
    tester = _get_tester()
    with pytest.raises(WrongParametersError) as err:
        tester.execute("--open")

    assert err.value.args[0] == "Specify a target to open in the browser."


# --- a single target: print and copy ---


@pytest.mark.parametrize(
    ("target", "label", "url"),
    [
        ("admin", "Admin UI", "https://ml.example.com:8001"),
        ("qconsole", "QConsole", "https://ml.example.com:8000/qconsole"),
        ("qc", "QConsole", "https://ml.example.com:8000/qconsole"),
        ("manage", "Monitoring Dashboard", "https://ml.example.com:8002/dashboard"),
        ("monitoring", "Monitoring Dashboard", "https://ml.example.com:8002/dashboard"),
        ("content", "content", "https://ml.example.com:8100"),
    ],
)
def test_target_prints_labelled_url_and_copies_bare_url(
    clipboard_process,
    target,
    label,
    url,
):
    tester = _get_tester()
    status = tester.execute(target)

    assert status == 0
    output = tester.io.fetch_output()
    assert label in output
    assert url in output
    assert "Copied to clipboard." in output
    clipboard_process.assert_called_once()
    assert clipboard_process.call_args.kwargs["input"] == url.encode("utf-8")


def test_unknown_app_server_id_is_rejected(clipboard_process):
    tester = _get_tester()
    with pytest.raises(NoSuchAppServerError):
        tester.execute("nope")

    clipboard_process.assert_not_called()


def test_clipboard_failure_is_non_fatal(clipboard_process):
    clipboard_process.side_effect = OSError

    tester = _get_tester()
    status = tester.execute("admin")

    assert status == 0
    output = tester.io.fetch_output()
    assert "Admin UI" in output
    assert "https://ml.example.com:8001" in output
    assert "Copied to clipboard." not in output
    assert "Could not copy to clipboard" in tester.io.fetch_error()


# --- --open: print and open, never copy ---


def test_open_launches_browser_without_copying(clipboard_process, browser_open):
    tester = _get_tester()
    status = tester.execute("admin --open")

    assert status == 0
    output = tester.io.fetch_output()
    assert "Admin UI" in output
    assert "https://ml.example.com:8001" in output
    assert "Opened in browser." in output
    assert "Copied to clipboard." not in output
    browser_open.assert_called_once_with("https://ml.example.com:8001")
    clipboard_process.assert_not_called()
