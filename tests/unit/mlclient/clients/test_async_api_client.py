import httpx
import pytest
import respx

from mlclient.calls import EvalCall
from mlclient.clients.api_client import AsyncApiClient
from mlclient.clients.http_client import AsyncHttpClient
from tests.utils.ml_mockers import MLRespXMocker


@pytest.fixture
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element as element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@pytest.mark.asyncio
@respx.mock
async def test_call(xquery):
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
    async with AsyncHttpClient() as http:
        api = AsyncApiClient(http)
        resp = await api.call(eval_call)

    assert resp.status_code == httpx.codes.OK
    assert "<new-parent><child/></new-parent>" in resp.text
