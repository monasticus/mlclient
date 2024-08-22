import pytest
import respx

from mlclient import MLResourceClient
from mlclient.calls import EvalCall
from tests.utils.response_builders import MLRespXMocker


@pytest.fixture()
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element as element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@respx.mock
def test_call(xquery):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
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
    with MLResourceClient() as client:
        resp = client.call(eval_call)

    assert resp.status_code == 200
    assert "<new-parent><child/></new-parent>" in resp.text
