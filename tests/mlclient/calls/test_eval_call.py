import pytest

from mlclient import exceptions
from mlclient.calls import EvalCall


@pytest.fixture()
def default_eval_call():
    """Return an EvalCall instance with a required parameter only."""
    return EvalCall(xquery="()")


def test_validation_neither_xquery_nor_javascript_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        EvalCall()

    expected_msg = "You must include either the xquery or the javascript parameter!"
    assert err.value.args[0] == expected_msg


def test_validation_xquery_and_javascript_param_are_none():
    with pytest.raises(exceptions.WrongParametersError) as err:
        EvalCall(xquery=None, javascript=None)

    expected_msg = "You must include either the xquery or the javascript parameter!"
    assert err.value.args[0] == expected_msg


def test_validation_xquery_and_javascript_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        EvalCall(xquery="()", javascript="[]")

    expected_msg = "You cannot include both the xquery and the javascript parameter!"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_eval_call):
    assert default_eval_call.endpoint == "/v1/eval"
    assert default_eval_call.ENDPOINT == "/v1/eval"
    assert EvalCall.ENDPOINT == "/v1/eval"


def test_method(default_eval_call):
    assert default_eval_call.method == "POST"


def test_parameters(default_eval_call):
    assert default_eval_call.params == {}


def test_headers(default_eval_call):
    assert default_eval_call.headers == {
        "accept": "multipart/mixed",
        "content-type": "application/x-www-form-urlencoded",
    }


def test_body_without_variables(default_eval_call):
    assert default_eval_call.body == {
        "xquery": "()",
    }


def test_body_with_variables():
    call = EvalCall(xquery="()",
                    variables={"custom-variable": "custom-value"})
    assert call.body == {
        "xquery": "()",
        "vars": '{"custom-variable": "custom-value"}',
    }


def test_body_is_normalized():
    xquery = """
    xquery version '1.0-ml';

    declare variable $data as xs:string? external;

    let $a =
        if (fn:empty($data)) then
            'default'
        else $data
    return $a
    """

    call = EvalCall(xquery=xquery,
                    variables={"data": "custom-value"})

    assert call.body == {  # No new line in the xquery code
        "xquery": "xquery version '1.0-ml'; "
                  "declare variable $data as xs:string? external; "
                  "let $a = if (fn:empty($data)) then 'default' else $data "
                  "return $a",
        "vars": '{"data": "custom-value"}',
    }


def test_fully_parametrized_xquery_call():
    call = EvalCall(xquery="()",
                    variables={"custom-variable": "custom-value"},
                    database="custom-db",
                    txid="custom-transaction-id")
    assert call.method == "POST"
    assert call.headers == {
        "accept": "multipart/mixed",
        "content-type": "application/x-www-form-urlencoded",
    }
    assert call.params == {
        "database": "custom-db",
        "txid": "custom-transaction-id",
    }
    assert call.body == {
        "xquery": "()",
        "vars": '{"custom-variable": "custom-value"}',
    }


def test_fully_parametrized_javascript_call():
    call = EvalCall(javascript="[]",
                    variables={"custom-variable": "custom-value"},
                    database="custom-db",
                    txid="custom-transaction-id")
    assert call.method == "POST"
    assert call.headers == {
        "accept": "multipart/mixed",
        "content-type": "application/x-www-form-urlencoded",
    }
    assert call.params == {
        "database": "custom-db",
        "txid": "custom-transaction-id",
    }
    assert call.body == {
        "javascript": "[]",
        "vars": '{"custom-variable": "custom-value"}',
    }
