import pytest

from mlclient import exceptions
from mlclient.calls.clientapi import EvalCall


@pytest.fixture
def default_eval_call():
    """Returns an EvalCall instance with a required parameter without any custom details"""
    return EvalCall(xquery="()")


def test_validation_neither_xquery_nor_javascript_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        EvalCall()

    assert err.value.args[0] == "You must include either the xquery or the javascript parameter!"


def test_validation_xquery_and_javascript_param_are_none():
    with pytest.raises(exceptions.WrongParameters) as err:
        EvalCall(xquery=None, javascript=None)

    assert err.value.args[0] == "You must include either the xquery or the javascript parameter!"


def test_validation_xquery_and_javascript_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        EvalCall(xquery="()", javascript="[]")

    assert err.value.args[0] == "You cannot include both the xquery and the javascript parameter!"


def test_endpoint(default_eval_call):
    assert default_eval_call.endpoint() == "/v1/eval"
    assert default_eval_call.ENDPOINT == "/v1/eval"
    assert EvalCall.ENDPOINT == "/v1/eval"


def test_method(default_eval_call):
    assert default_eval_call.method() == "POST"


def test_headers(default_eval_call):
    assert {
        "accept": "multipart/mixed",
        "content-type": "application/x-www-form-urlencoded"
    } == default_eval_call.headers()


def test_body_without_variables(default_eval_call):
    assert {
        "xquery": "()"
    } == default_eval_call.body()


def test_body_with_variables(default_eval_call):
    call = EvalCall(xquery="()",
                    variables={"custom-variable": "custom-value"})
    assert {
        "xquery": "()",
        "vars": '{"custom-variable": "custom-value"}'
    } == call.body()


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

    assert {  # No new line in the xquery code
        "xquery": "xquery version '1.0-ml'; "
                  "declare variable $data as xs:string? external; "
                  "let $a = if (fn:empty($data)) then 'default' else $data "
                  "return $a",
        "vars": '{"data": "custom-value"}'
    } == call.body()


def test_fully_parametrized_xquery_call():
    call = EvalCall(xquery="()",
                    variables={"custom-variable": "custom-value"},
                    database="custom-db",
                    txid="custom-transaction-id")
    assert call.method() == "POST"
    assert {
        "accept": "multipart/mixed",
        "content-type": "application/x-www-form-urlencoded"
    } == call.headers()
    assert {
         "database": "custom-db",
         "txid": "custom-transaction-id"
    } == call.params()
    assert {
        "xquery": "()",
        "vars": '{"custom-variable": "custom-value"}'
    } == call.body()


def test_fully_parametrized_javascript_call():
    call = EvalCall(javascript="[]",
                    variables={"custom-variable": "custom-value"},
                    database="custom-db",
                    txid="custom-transaction-id")
    assert call.method() == "POST"
    assert {
        "accept": "multipart/mixed",
        "content-type": "application/x-www-form-urlencoded"
    } == call.headers()
    assert {
         "database": "custom-db",
         "txid": "custom-transaction-id"
    } == call.params()
    assert {
        "javascript": "[]",
        "vars": '{"custom-variable": "custom-value"}'
    } == call.body()
