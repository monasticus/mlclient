import pytest
import responses

from mlclient import MLResourceClient
from mlclient.calls import EvalCall
from tests.tools import MLResponseBuilder


@pytest.fixture()
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element as element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@responses.activate
def test_call(xquery):
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_body(
        {
            "xquery": "xquery version '1.0-ml';"
            " declare variable $element as element() external;"
            " <new-parent>{$element/child::element()}</new-parent>",
            "vars": '{"element": "<parent><child/></parent>"}',
        },
    )
    builder.with_response_body_multipart_mixed()
    builder.with_response_status(200)
    builder.with_response_body_part("element()", "<new-parent><child/></new-parent>")
    builder.build_post()

    eval_call = EvalCall(
        xquery=xquery,
        variables={"element": "<parent><child/></parent>"},
    )
    with MLResourceClient(auth_method="digest") as client:
        resp = client.call(eval_call)
        MLResponseBuilder.generate_builder_code(resp)

    assert resp.status_code == 200
    assert "<new-parent><child/></new-parent>" in resp.text
