from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
import respx

from mlclient.clients.api_client import AsyncApiClient
from mlclient.clients.http_client import AsyncHttpClient
from mlclient.exceptions import (
    MarkLogicError,
    UnsupportedFileExtensionError,
    WrongParametersError,
)
from mlclient.services.eval import LOCAL_NS, AsyncEvalService
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


@pytest_asyncio.fixture
async def svc():
    async with AsyncHttpClient() as http:
        yield AsyncEvalService(AsyncApiClient(http))


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_xquery_empty(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.xquery(code)

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_xquery_single_item(svc):
    code = "''"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    resp = await svc.xquery(code)

    assert resp == ""


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_xquery_multiple_items(svc):
    code = "('',1)"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.with_response_body_part("integer", "1")
    ml_mocker.mock_post()

    resp = await svc.xquery(code)

    assert resp == ["", 1]


@pytest.mark.asyncio
@respx.mock
async def test_eval_xqy_alias(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.xqy(code)

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_javascript_empty(svc):
    code = "Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.javascript(code)

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_javascript_single_item(svc):
    code = "''"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    resp = await svc.javascript(code)

    assert resp == ""


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_javascript_multiple_items(svc):
    code = "Sequence.from(['', 1]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.with_response_body_part("integer", "1")
    ml_mocker.mock_post()

    resp = await svc.javascript(code)

    assert resp == ["", 1]


@pytest.mark.asyncio
@respx.mock
async def test_eval_js_alias(svc):
    code = "Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.js(code)

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_variables_explicit(svc):
    code = "declare variable $VARIABLE as xs:string external; $VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": '{"VARIABLE": "X"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, variables={"VARIABLE": "X"})

    assert resp == "X"


@pytest.mark.asyncio
@respx.mock
async def test_eval_variables_using_kwargs(svc):
    code = "declare variable $VARIABLE as xs:string external; $VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": '{"VARIABLE": "X"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, VARIABLE="X")

    assert resp == "X"


@pytest.mark.asyncio
@respx.mock
async def test_eval_variables_explicit_with_kwargs(svc):
    code = (
        "declare variable $INTEGER1 external; "
        "declare variable $INTEGER2 external; "
        "$INTEGER1 + $INTEGER2"
    )

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": '{"INTEGER1": 1, "INTEGER2": 2}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("integer", "3")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, variables={"INTEGER1": 1}, INTEGER2=2)

    assert resp == 3


@pytest.mark.asyncio
@respx.mock
async def test_eval_variables_using_namespace(svc):
    code = "declare variable $local:VARIABLE as xs:string external; $local:VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": f'{{"{{{LOCAL_NS}}}VARIABLE": "X"}}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, variables={f"{{{LOCAL_NS}}}VARIABLE": "X"})

    assert resp == "X"


@pytest.mark.asyncio
@respx.mock
async def test_eval_using_database_param(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.xquery(code, database="Documents")

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_using_txid_param(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.xquery(code, txid="transaction-id")

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_file_xquery(svc):
    code = 'xquery version "1.0-ml"; ()'

    ml_mocker = MLRespXMocker(use_router=False)
    for ext in ["xq", "xql", "xqm", "xqu", "xquery", "xqy"]:
        ml_mocker.with_url("http://localhost:8000/v1/eval")
        ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
        ml_mocker.with_request_body({"xquery": code})
        ml_mocker.with_response_code(200)
        ml_mocker.with_empty_response_body()
        ml_mocker.mock_post()

        file_path = resources_utils.get_test_resource_path(
            __file__,
            f"xquery-code.{ext}",
        )
        resp = await svc.file(file_path)

        assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_file_javascript(svc):
    code = "'use strict'; Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    for ext in ["js", "sjs"]:
        ml_mocker.with_url("http://localhost:8000/v1/eval")
        ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
        ml_mocker.with_request_body({"javascript": code})
        ml_mocker.with_response_code(200)
        ml_mocker.with_empty_response_body()
        ml_mocker.mock_post()

        file_path = resources_utils.get_test_resource_path(
            __file__,
            f"javascript-code.{ext}",
        )
        resp = await svc.file(file_path)

        assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_with_marklogic_error(svc):
    error_path = resources_utils.get_test_resource_path(
        __file__,
        "marklogic-error.html",
    )
    code = "declare variable $local:VARIABLE external; $local:VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("text/html; charset=utf-8")
    ml_mocker.with_response_body(Path(error_path).read_bytes())
    ml_mocker.mock_post()

    with pytest.raises(MarkLogicError) as err:
        await svc.xquery(code)

    expected_msg = (
        "XDMP-EXTVAR: (err:XPDY0002) "
        "declare variable $local:VARIABLE external;  "
        '-- Undefined external variable xs:QName("local:VARIABLE")\n'
        "in /eval, at 1:43 [1.0-ml]"
    )
    assert err.value.args[0] == expected_msg


@pytest.mark.asyncio
async def test_eval_execute_rejects_file_with_xquery(svc):
    with pytest.raises(WrongParametersError) as err:
        await svc.execute(file="code.xqy", xq="()")

    assert "file" in err.value.args[0]
    assert "xquery" in err.value.args[0]


@pytest.mark.asyncio
async def test_eval_execute_rejects_file_with_javascript(svc):
    with pytest.raises(WrongParametersError) as err:
        await svc.execute(file="code.sjs", js="[];")

    assert "file" in err.value.args[0]
    assert "javascript" in err.value.args[0]


@pytest.mark.asyncio
async def test_eval_file_unknown_extension(svc):
    with pytest.raises(UnsupportedFileExtensionError) as err:
        await svc.file("unknown-extension.txt")

    assert err.value.args[0] == (
        "Unknown file extension! "
        "Supported extensions are: "
        "xq, xql, xqm, xqu, xquery, xqy, js, sjs"
    )


@pytest.mark.asyncio
@respx.mock
async def test_eval_with_str_output_type(svc):
    code = "element root {}"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, output_type=str)

    assert isinstance(resp, str)
    assert resp == "<root/>"


@pytest.mark.asyncio
@respx.mock
async def test_eval_with_bytes_output_type(svc):
    code = "element root {}"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, output_type=bytes)

    assert isinstance(resp, bytes)
    assert resp == b"<root/>"
