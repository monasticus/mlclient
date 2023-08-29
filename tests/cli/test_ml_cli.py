import sys

import pytest
from cleo.testers.command_tester import CommandTester

import mlclient
from cli import main
from cli.ml_cli import MLCLIentApplication
from tests import tools

test_helper = tools.TestHelper("test")


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    test_helper.setup_environment()

    yield

    # Teardown
    test_helper.clean_environment()


def test_main_sys_exit_1():
    with pytest.raises(SystemExit) as err:
        main()
    assert err.value.args[0] == 1


def test_main_sys_exit_0():
    sys.argv = ["ml"]
    with pytest.raises(SystemExit) as err:
        main()
    assert err.value.args[0] == 0


def test_app_properties():
    app = MLCLIentApplication()
    assert app.display_name == "MLCLIent"
    assert app.version == mlclient.__version__


def test_command_call_logs():
    tester = _get_tester("call logs")
    tester.execute("-e test")

    command_environment = tester.command.option("environment")
    command_app_server = tester.command.option("app-server")

    assert command_environment == "test"
    assert command_app_server == "manage"
    assert "Getting logs from http://localhost:8002" in tester.io.fetch_output()
    test_helper.confirm_last_request(
        app_server=command_app_server,
        request_method="GET",
        request_url="/manage/v2/logs?format=json&filename=8002_ErrorLog.txt")


def _get_tester(
        command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)
