import httpx
import pytest
import respx

from mlclient import MLClient
from mlclient.calls import EvalCall
from mlclient.clients.api_client import ApiClient, AsyncApiClient
from mlclient.clients.http_client import AsyncHttpClient, HttpClient
from tests.utils.ml_mockers import MLRespXMocker


@pytest.fixture
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element as element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@respx.mock
def test_call(xquery):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": "xquery version '1.0-ml';"
            " declare variable $element as element() external;"
            " <new-parent>{$element/child::element()}</new-parent>",
            "vars": '{"element": "<parent><child/></parent>"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element()", "<new-parent><child/></new-parent>")
    ml_mocker.mock_post()

    eval_call = EvalCall(
        xquery=xquery,
        variables={"element": "<parent><child/></parent>"},
    )
    with MLClient() as ml:
        resp = ml.rest.call(eval_call)

    assert resp.status_code == httpx.codes.OK
    assert "<new-parent><child/></new-parent>" in resp.text


@respx.mock
def test_call_forwards_timeout_to_transport():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(200, text="()"),
    )
    with HttpClient() as http:
        ApiClient(http).call(EvalCall(xquery="()"), timeout=2)
    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


@pytest.mark.asyncio
@respx.mock
async def test_async_call_forwards_timeout_to_transport():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(200, text="()"),
    )
    async with AsyncHttpClient() as http:
        await AsyncApiClient(http).call(EvalCall(xquery="()"), timeout=2)
    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }
