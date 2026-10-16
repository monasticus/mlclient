from __future__ import annotations

import pytest
import respx
from cleo.testers.command_tester import CommandTester

from mlclient.cli import MLCLIentApplication
from mlclient.env import MLEnvironment
from mlclient.exceptions import WrongParametersError
from tests.utils.ml_mockers import MLRespXMocker

MODULE = "/ext/mlclient/words.xqy"


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
            {
                "id": "content",
                "port": 8100,
                "auth": "basic",
            },
        ],
    }
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config):
    target = "mlclient.env.MLEnvironment.load"
    mocker.patch(target, return_value=ml_config)


# --- arguments and options ---


@respx.mock
def test_command_invoke_basic():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    tester.execute(f"-e test {MODULE}")

    assert tester.status_code == 0
    assert tester.command.argument("module") == MODULE
    assert tester.command.option("environment") == "test"
    assert tester.command.option("connection") is None
    assert tester.command.option("var") == []
    assert tester.command.option("database") is None
    assert tester.command.option("txid") is None


@respx.mock
def test_command_invoke_custom_connection():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8100/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    tester.execute(f"-e test -c content {MODULE}")

    assert tester.status_code == 0
    assert tester.command.option("connection") == "content"


@respx.mock
def test_command_invoke_with_vars():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"module": MODULE, "vars": '{"word1": "hello", "word2": "world"}'},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello world")
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    tester.execute(f"-e test {MODULE} --var word1=hello --var word2=world")

    assert tester.status_code == 0
    assert tester.command.option("var") == ["word1=hello", "word2=world"]


@respx.mock
def test_command_invoke_var_value_with_equals_sign():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE, "vars": '{"filter": "a=b"}'})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "a=b")
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    tester.execute(f"-e test {MODULE} --var filter=a=b")

    assert tester.status_code == 0


def test_command_invoke_var_without_value():
    tester = _get_tester("invoke")
    with pytest.raises(WrongParametersError) as err:
        tester.execute(f"-e test {MODULE} --var word1")

    assert str(err.value) == "A variable must be passed as name=value, got: word1"


@respx.mock
def test_command_invoke_custom_database():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/invoke")
    ml_mocker.with_request_param("database", "custom-db")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    tester.execute(f"-e test -d custom-db {MODULE}")

    assert tester.status_code == 0
    assert tester.command.option("database") == "custom-db"


@respx.mock
def test_command_invoke_custom_txid():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/invoke")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    tester.execute(f"-e test -t transaction-id {MODULE}")

    assert tester.status_code == 0
    assert tester.command.option("txid") == "transaction-id"


# --- output ---


@respx.mock
def test_command_invoke_output():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"module": MODULE, "vars": '{"word1": "hello", "word2": "world"}'},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello")
    ml_mocker.with_response_body_part("string", "world")
    ml_mocker.with_response_body_part("string", "hello world")
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    tester.execute(f"-e test {MODULE} --var word1=hello --var word2=world")

    assert tester.io.fetch_output() == (
        "Invoking module using REST App-Server http://localhost:8002\n\n"
        "hello\nworld\nhello world\n"
    )


@respx.mock
def test_command_invoke_formats_results_by_default():
    result = "<root><item>one</item><item>two</item></root>"
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element()", result)
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    assert tester.execute(MODULE) == 0
    assert tester.io.fetch_output() == (
        "Invoking module using REST App-Server http://localhost:8002\n\n"
        "<root>\n  <item>one</item>\n  <item>two</item>\n</root>\n"
    )


@respx.mock
def test_command_invoke_no_pretty_preserves_xml():
    result = "<root><item>one</item></root>"
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element()", result)
    ml_mocker.mock_post()

    tester = _get_tester("invoke")
    assert tester.execute(f"{MODULE} --no-pretty") == 0
    assert tester.io.fetch_output() == (
        "Invoking module using REST App-Server http://localhost:8002\n\n"
        + result
        + "\n"
    )


def _get_tester(
    command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)
