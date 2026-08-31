from __future__ import annotations

import httpx
import pytest

from mlclient import MLClient, MLResponseParser
from mlclient.calls import EvalCall

EVAL_XQUERY = (
    "xquery version '1.0-ml';\n\n"
    "declare variable $element as element() external;\n\n"
    "<new-parent>{$element/child::element()}</new-parent>"
)


@pytest.mark.ml_access
def test_eval_call_returns_multipart_response():
    call = EvalCall(
        xquery=EVAL_XQUERY,
        variables={"element": "<parent><child/></parent>"},
    )

    with MLClient() as ml:
        resp = ml.rest.call(call)

    assert resp.status_code == httpx.codes.OK
    assert MLResponseParser.parse(resp, str) == "<new-parent><child/></new-parent>"
