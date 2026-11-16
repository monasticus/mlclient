from __future__ import annotations

import httpx
import pytest

from mlclient import MLClient
from mlclient.calls import EvalCall
from mlclient.exceptions import MarkLogicError
from mlclient.responses import MLResponseParser

EVAL_XQUERY = (
    "xquery version '1.0-ml';\n\n"
    "declare variable $element external;\n\n"
    "<new-parent>{xdmp:unquote($element)/parent/child}</new-parent>"
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


@pytest.mark.ml_access
@pytest.mark.parametrize("with_headers", [False, True])
def test_parsing_an_error_response_raises_marklogic_error(with_headers):
    with MLClient() as ml:
        resp = ml.rest.documents.get(uri="/mlclient-integration/missing-doc.json")

    parse = (
        MLResponseParser.parse_with_headers if with_headers else MLResponseParser.parse
    )
    with pytest.raises(MarkLogicError, match="RESTAPI-NODOCUMENT") as raised:
        parse(resp)

    assert raised.value.status_code == httpx.codes.NOT_FOUND
    assert raised.value.message_code == "RESTAPI-NODOCUMENT"
