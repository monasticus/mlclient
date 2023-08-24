import os
import shutil
import sys
from pathlib import Path

import pytest
from cleo.testers.command_tester import CommandTester

import mlclient
from cli.ml_cli import MLCLIentApplication
from cli import main
from mlclient import constants
from tests import tools


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    ml_client_dir = Path(constants.ML_CLIENT_DIR)
    if not ml_client_dir.exists() or not ml_client_dir.is_dir():
        ml_client_dir.mkdir()
    for file_name in tools.list_resources(__file__):
        file_path = tools.get_test_resource_path(__file__, file_name)
        shutil.copy(file_path, constants.ML_CLIENT_DIR)

    yield

    # Teardown
    for file_name in tools.list_resources(__file__):
        Path(f"{constants.ML_CLIENT_DIR}/{file_name}").unlink()
    if ml_client_dir.exists() and not os.listdir(constants.ML_CLIENT_DIR):
        ml_client_dir.rmdir()


def test_main_sys_exit_0():
    sys.argv = ["ml"]
    with pytest.raises(SystemExit) as err:
        main()
        assert err.value.args[0] == 0


def test_main_sys_exit_1():
    with pytest.raises(SystemExit) as err:
        main()
        assert err.value.args[0] == 1


def test_app_properties():
    app = MLCLIentApplication()
    assert app.display_name == "MLCLIent"
    assert app.version == mlclient.__version__


def test_command_call_logs():
    tester = _get_tester("call logs")
    tester.execute("-e test")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") == "manage"

    assert "Getting logs from http://localhost:8002" in tester.io.fetch_output()


def _get_tester(
        command_name: str,
):
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)
