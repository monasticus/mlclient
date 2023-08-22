import sys
from io import StringIO

import pytest

import mlclient
from cli import ml_cli


def test_cli_version():
    sys.argv = ["ml", "--version"]

    output_redirection = StringIO()
    sys.stdout = output_redirection

    try:
        ml_cli.main()
        pytest.fail("'ml --version' should invoke system exit")
    except SystemExit:
        assert output_redirection.getvalue() == f"MLCLIent v{mlclient.__version__}\n"
        sys.stdout = sys.__stdout__
