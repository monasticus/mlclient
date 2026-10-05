from __future__ import annotations

import json

import pytest
import respx
from cleo.testers.command_tester import CommandTester

from mlclient import MLClientManager
from mlclient.cli import MLCLIentApplication
from mlclient.env import MLEnvironment
from mlclient.exceptions import WrongParametersError
from mlclient.functions.xqy import cts
from mlclient.services import EvalService
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

SEARCH_XQUERY = resources_utils.read_test_resource_text(
    __file__, "search.xqy",
).removesuffix("\n")


@pytest.fixture(autouse=True)
def environment_loader(mocker):
    config = MLEnvironment(
        **{
            "app-name": "my-marklogic-app",
            "host": "localhost",
            "username": "admin",
            "password": "admin",
            "protocol": "http",
            "app-servers": [{"id": "content", "port": 8100, "rest": True}],
        },
    )
    return mocker.patch("mlclient.env.MLEnvironment.load", return_value=config)


@respx.mock
def test_command_sample_sends_search_request():
    variables = {
        "v0": "/order",
        "v1": "format-xml",
        "v2": "1",
        "v3": "2",
        "v4": "cts:search(/order, (), $v1)[$v2 to $v3]",
    }
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8100/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"xquery": SEARCH_XQUERY, "vars": json.dumps(variables)},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()
    tester = _get_tester()

    assert tester.execute("order --limit 2 -c content") == 0
    assert tester.io.fetch_output() == ""


def test_command_sample_root(mocker):
    evaluate = mocker.patch.object(
        EvalService,
        "expression",
        return_value="<order><item>one</item></order>",
    )
    tester = _get_tester()

    assert tester.execute("order") == 0

    evaluate.assert_called_once_with(
        cts.search("/order", options="format-xml").pos([1, 1]),
        output_type=str,
    )
    assert tester.io.fetch_output() == "<order>\n  <item>one</item>\n</order>\n"


def test_command_sample_document(mocker):
    evaluate = mocker.patch.object(
        EvalService,
        "expression",
        return_value="<order><item/></order>",
    )
    tester = _get_tester()

    assert tester.execute("") == 0

    evaluate.assert_called_once_with(
        cts.search("/", options="format-xml").pos([1, 1]),
        output_type=str,
    )
    assert tester.io.fetch_output() == "<order>\n  <item/>\n</order>\n"


def test_command_sample_path(mocker):
    evaluate = mocker.patch.object(
        EvalService,
        "expression",
        return_value="<item>one</item>",
    )
    tester = _get_tester()

    assert tester.execute("/order/item") == 0

    evaluate.assert_called_once_with(
        cts.search("/order/item", options="format-xml").pos([1, 1]),
        output_type=str,
    )
    assert tester.io.fetch_output() == "<item>one</item>\n"


def test_command_sample_limit(mocker):
    evaluate = mocker.patch.object(
        EvalService,
        "expression",
        return_value=["<item>one</item>", "<item>two</item>"],
    )
    tester = _get_tester()

    assert tester.execute("/order/item --limit 2") == 0

    evaluate.assert_called_once_with(
        cts.search("/order/item", options="format-xml").pos([1, 2]),
        output_type=str,
    )
    assert tester.io.fetch_output() == "<item>one</item>\n<item>two</item>\n"


def test_command_sample_relative_path(mocker):
    evaluate = mocker.patch.object(EvalService, "expression", return_value=[])

    assert _get_tester().execute("order/item") == 0

    evaluate.assert_called_once_with(
        cts.search("order/item", options="format-xml").pos([1, 1]),
        output_type=str,
    )


def test_command_sample_limit_short_option(mocker):
    evaluate = mocker.patch.object(EvalService, "expression", return_value=[])

    assert _get_tester().execute("order -l 2") == 0

    evaluate.assert_called_once_with(
        cts.search("/order", options="format-xml").pos([1, 2]),
        output_type=str,
    )


def test_command_sample_connection(mocker):
    mocker.patch.object(EvalService, "expression", return_value=[])
    factory = mocker.spy(MLClientManager, "get_client")

    assert _get_tester().execute("order -c content") == 0

    factory.assert_called_once_with(mocker.ANY, "content")
    assert str(factory.spy_return.http.base_url) == "http://localhost:8100"


def test_command_sample_connection_port(mocker):
    mocker.patch.object(EvalService, "expression", return_value=[])
    factory = mocker.spy(MLClientManager, "get_client")

    assert _get_tester().execute("order -c 8101") == 0

    factory.assert_called_once_with(mocker.ANY, port=8101)
    assert str(factory.spy_return.http.base_url) == "http://localhost:8101"


def test_command_sample_environment(mocker, environment_loader):
    mocker.patch.object(EvalService, "expression", return_value=[])

    assert _get_tester().execute("order -e dev") == 0
    environment_loader.assert_called_once_with("dev")


@pytest.mark.parametrize("json_option", ["--json", "-j"])
def test_command_sample_json_document(mocker, json_option):
    evaluate = mocker.patch.object(
        EvalService,
        "expression",
        return_value='{"name":"zażółć"}',
    )
    tester = _get_tester()

    assert tester.execute(json_option) == 0

    evaluate.assert_called_once_with(
        cts.search("/", options="format-json").pos([1, 1]),
        output_type=str,
    )
    assert tester.io.fetch_output() == '{\n  "name": "zażółć"\n}\n'


def test_command_sample_json_property(mocker):
    evaluate = mocker.patch.object(
        EvalService,
        "expression",
        return_value='{"city":"Warsaw"}',
    )
    tester = _get_tester()

    assert tester.execute("address --json") == 0

    evaluate.assert_called_once_with(
        cts.search("/address", options="format-json").pos([1, 1]),
        output_type=str,
    )
    assert tester.io.fetch_output() == '{\n  "city": "Warsaw"\n}\n'


def test_command_sample_json_array(mocker):
    evaluate = mocker.patch.object(EvalService, "expression", return_value="[1,2]")
    tester = _get_tester()

    assert tester.execute("--json") == 0

    evaluate.assert_called_once_with(
        cts.search("/", options="format-json").pos([1, 1]),
        output_type=str,
    )
    assert tester.io.fetch_output() == "[\n  1,\n  2\n]\n"


@pytest.mark.parametrize("content", ["true", "null", "42", '"one"'])
def test_command_sample_json_scalar_document(mocker, content):
    mocker.patch.object(EvalService, "expression", return_value=content)
    tester = _get_tester()

    assert tester.execute("--json") == 0
    assert tester.io.fetch_output() == content + "\n"


def test_command_sample_no_pretty_xml(mocker):
    content = '<order>\r\n    <item name="one" />\r\n</order>'
    mocker.patch.object(EvalService, "expression", return_value=content)
    tester = _get_tester()

    assert tester.execute("order --no-pretty") == 0
    assert tester.io.fetch_output() == content + "\n"


def test_command_sample_empty_results(mocker):
    mocker.patch.object(EvalService, "expression", return_value=[])
    tester = _get_tester()

    assert tester.execute("missing") == 0
    assert tester.io.fetch_output() == ""


def test_command_sample_maximum_limit(mocker):
    evaluate = mocker.patch.object(EvalService, "expression", return_value=[])

    assert _get_tester().execute("order --limit 100") == 0

    evaluate.assert_called_once_with(
        cts.search("/order", options="format-xml").pos([1, 100]),
        output_type=str,
    )


@pytest.mark.parametrize("limit", ["0", "-1", "101", "1000", "1.5", "bad"])
def test_command_sample_invalid_limit(limit):
    with pytest.raises(WrongParametersError) as error:
        _get_tester().execute(f"order --limit={limit}")
    assert str(error.value) == "The sample limit must be an integer between 1 and 100."


def test_command_sample_empty_path():
    with pytest.raises(WrongParametersError) as error:
        _get_tester().execute("' '")
    assert str(error.value) == "The sample root or path cannot be empty."


def _get_tester() -> CommandTester:
    return CommandTester(MLCLIentApplication().find("sample"))
