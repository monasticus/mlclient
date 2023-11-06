import pytest

from mlclient import MLResourceClient
from mlclient.calls import EvalCall


@pytest.fixture()
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element as element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@pytest.mark.ml_access()
def test_call(xquery):
    eval_call = EvalCall(
        xquery=xquery,
        variables={"element": "<parent><child/></parent>"},
    )
    with MLResourceClient(auth_method="digest") as client:
        resp = client.call(eval_call)

    assert resp.status_code == 200
    assert "<new-parent><child/></new-parent>" in resp.text
