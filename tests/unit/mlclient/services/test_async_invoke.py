from __future__ import annotations

import httpx
import pytest
import pytest_asyncio
import respx

from mlclient import AsyncMLClient
from mlclient.exceptions import MarkLogicError, WrongParametersError
from mlclient.xquery import LOCAL_NS_URI
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

MODULE = "/ext/mlclient/words.xqy"


@pytest_asyncio.fixture
async def ml() -> AsyncMLClient:
    async with AsyncMLClient() as client:
        yield client


# --- results ---


@pytest.mark.asyncio
@respx.mock
async def test_module_with_empty_result(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE)

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_module_with_single_item(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello world")
    ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE)

    assert result == "hello world"


@pytest.mark.asyncio
@respx.mock
async def test_module_with_multiple_items(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"module": MODULE, "vars": '{"word1": "hello", "word2": "world"}'},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello")
    ml_mocker.with_response_body_part("string", "world")
    ml_mocker.with_response_body_part("string", "hello world")
    ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE, word1="hello", word2="world")

    assert result == ["hello", "world", "hello world"]


@pytest.mark.asyncio
@respx.mock
async def test_javascript_module_is_sent_by_path_only(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"module": "/ext/mlclient/words.sjs", "vars": '{"word1": "hello"}'},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello")
    ml_mocker.mock_post()

    result = await ml.invoke.module("/ext/mlclient/words.sjs", word1="hello")

    assert result == "hello"


@pytest.mark.asyncio
@respx.mock
async def test_module_with_str_output_type(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE, output_type=str)

    assert isinstance(result, str)
    assert result == "<root/>"


@pytest.mark.asyncio
@respx.mock
async def test_module_with_bytes_output_type(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE, output_type=bytes)

    assert isinstance(result, bytes)
    assert result == b"<root/>"


# --- variables ---


@pytest.mark.asyncio
@respx.mock
async def test_module_variables_explicit(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE, "vars": '{"word1": "hello"}'})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello")
    ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE, variables={"word1": "hello"})

    assert result == "hello"


@pytest.mark.asyncio
@respx.mock
async def test_module_variables_explicit_with_kwargs(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"module": MODULE, "vars": '{"word1": "hello", "word2": "world"}'},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello world")
    ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE, variables={"word1": "hello"}, word2="world")

    assert result == "hello world"


@pytest.mark.asyncio
@respx.mock
async def test_module_kwargs_override_explicit_variables(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE, "vars": '{"word1": "hi"}'})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hi")
    ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE, variables={"word1": "hello"}, word1="hi")

    assert result == "hi"


@pytest.mark.asyncio
@respx.mock
async def test_module_keeps_caller_variables_unchanged(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"module": MODULE, "vars": '{"word1": "hello", "word2": "world"}'},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello world")
    ml_mocker.mock_post()
    variables = {"word1": "hello"}

    await ml.invoke.module(MODULE, variables=variables, word2="world")

    assert variables == {"word1": "hello"}


@pytest.mark.asyncio
@respx.mock
async def test_module_variables_using_namespace(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"module": MODULE, "vars": f'{{"{{{LOCAL_NS_URI}}}word1": "hello"}}'},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "hello")
    ml_mocker.mock_post()

    result = await ml.invoke.module(
        MODULE,
        variables={f"{{{LOCAL_NS_URI}}}word1": "hello"},
    )

    assert result == "hello"


# --- timeout ---


@pytest.mark.asyncio
@respx.mock
async def test_module_timeout_reaches_transport_and_is_not_a_module_variable(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()

    await ml.invoke.module(MODULE, timeout=2)

    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


@pytest.mark.asyncio
@respx.mock
async def test_module_variable_named_timeout_is_sent_as_module_variable(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE, "vars": '{"timeout": 30}'})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("integer", "30")
    route = ml_mocker.mock_post()

    result = await ml.invoke.module(MODULE, variables={"timeout": 30}, timeout=2)

    assert result == 30
    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


# --- errors ---


@pytest.mark.asyncio
async def test_module_rejects_blank_path_without_request(ml):
    with (
        respx.mock(assert_all_called=False) as router,
        pytest.raises(WrongParametersError) as err,
    ):
        await ml.invoke.module("  ")

    assert str(err.value) == "You must include the module parameter!"
    assert router.calls.call_count == 0


@pytest.mark.asyncio
@respx.mock
async def test_module_not_found(ml):
    error_body = resources_utils.read_test_resource_bytes(
        __file__,
        "marklogic-error.html",
    )

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": "/ext/mlclient/missing.xqy"})
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("text/html; charset=utf-8")
    ml_mocker.with_response_body(error_body)
    ml_mocker.mock_post()

    with pytest.raises(MarkLogicError) as err:
        await ml.invoke.module("/ext/mlclient/missing.xqy")

    expected_msg = (
        "XDMP-MODNOTFOUND: (err:XQST0059) "
        "Module /ext/mlclient/missing.xqy not found\n"
        "in /ext/mlclient/missing.xqy [1.0-ml]"
    )
    assert str(err.value) == expected_msg


@pytest.mark.asyncio
@respx.mock
async def test_module_preserves_bodyless_http_failure(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/invoke")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"module": MODULE})
    ml_mocker.with_response_code(403)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()

    with pytest.raises(httpx.HTTPStatusError) as raised:
        await ml.invoke.module(MODULE)

    assert route.call_count == 1
    assert raised.value.response.url == route.calls.last.request.url
    assert raised.value.response.status_code == 403


# --- database and transaction scope ---


@pytest.mark.asyncio
@respx.mock
async def test_module_without_scope(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    result = await ml.invoke.module(MODULE)

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_module_with_scope_kwargs(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    result = await ml.invoke.module(MODULE, database="request-db", txid="request-tx")

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_module_inherits_service_scope(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    result = await ml.invoke(database="service-db", txid="service-tx").module(MODULE)

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_module_scope_kwargs_override_service_scope(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    result = await ml.invoke(database="service-db", txid="service-tx").module(
        MODULE,
        database="request-db",
        txid="request-tx",
    )

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_module_scope_kwargs_clear_service_database(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    result = await ml.invoke(database="service-db", txid="service-tx").module(
        MODULE,
        database=None,
    )

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_module_scope_kwargs_clear_service_transaction(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.mock_post()

    result = await ml.invoke(database="service-db", txid="service-tx").module(
        MODULE,
        txid=None,
    )

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_invoke_scope_keeps_module_variables_separate(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE, "vars": '{"word1": "hello"}'})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "catalog")
    mocker.mock_post()

    await ml.invoke(database="catalog").module(MODULE, word1="hello")


@pytest.mark.asyncio
@respx.mock
async def test_overriding_scope_on_service_copy_preserves_original_scope(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.mock_post()
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-2")
    mocker.mock_post()

    original_service = ml.invoke(database="catalog", txid="tx-1")
    overridden_scope_service = original_service(txid="tx-2")
    await overridden_scope_service.module(MODULE)
    await original_service.module(MODULE)


@pytest.mark.asyncio
@respx.mock
async def test_clearing_scope_on_service_copy_preserves_original_scope(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.mock_post()
    mocker.with_url("http://localhost:8000/v1/invoke")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"module": MODULE})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    original_service = ml.invoke(database="catalog", txid="tx-1")
    cleared_scope_service = original_service(database=None, txid=None)
    await cleared_scope_service.module(MODULE)
    await original_service.module(MODULE)
