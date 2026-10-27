import pytest

from mlclient import exceptions
from mlclient.calls import InvokeCall


@pytest.fixture
def default_invoke_call():
    """Returns an InvokeCall instance"""
    return InvokeCall(module="/ext/mlclient/report.xqy")


@pytest.mark.parametrize("module", [None, "", "   "])
def test_validation_module_param(module):
    with pytest.raises(exceptions.WrongParametersError) as err:
        InvokeCall(module=module)

    assert str(err.value) == "You must include the module parameter!"


def test_endpoint(default_invoke_call):
    assert default_invoke_call.endpoint == "/v1/invoke"


def test_method(default_invoke_call):
    assert default_invoke_call.method == "POST"


def test_parameters(default_invoke_call):
    assert default_invoke_call.params == {}


def test_headers(default_invoke_call):
    assert default_invoke_call.headers == {
        "Accept": "multipart/mixed",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_body(default_invoke_call):
    assert default_invoke_call.body == {"module": "/ext/mlclient/report.xqy"}


def test_body_with_variables():
    call = InvokeCall(
        module="/ext/mlclient/report.xqy",
        variables={"custom-variable": "custom-value"},
    )
    assert call.body == {
        "module": "/ext/mlclient/report.xqy",
        "vars": '{"custom-variable": "custom-value"}',
    }


def test_body_with_empty_variables():
    call = InvokeCall(module="/ext/mlclient/report.xqy", variables={})
    assert call.body == {"module": "/ext/mlclient/report.xqy"}


def test_fully_parametrized_call():
    call = InvokeCall(
        module="/ext/mlclient/report.xqy",
        variables={"custom-variable": "custom-value"},
        database="Documents",
        txid="12345",
    )
    assert call.method == "POST"
    assert call.endpoint == "/v1/invoke"
    assert call.headers == {
        "Accept": "multipart/mixed",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    assert call.params == {
        "database": "Documents",
        "txid": "12345",
    }
    assert call.body == {
        "module": "/ext/mlclient/report.xqy",
        "vars": '{"custom-variable": "custom-value"}',
    }
