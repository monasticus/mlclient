from __future__ import annotations

import sys

import pytest

import mlclient
from mlclient.cli import MLCLIentApplication, main


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
    assert app.name == "ml"
    assert app.display_name == "MLCLIent"
    assert app.version == mlclient.__version__
