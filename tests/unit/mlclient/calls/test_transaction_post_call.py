import pytest

from mlclient import exceptions
from mlclient.calls import TransactionPostCall


@pytest.fixture
def default_transaction_post_call():
    """Returns a TransactionPostCall instance"""
    return TransactionPostCall(txid="12345", result="commit")


def test_validation_result_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        TransactionPostCall(txid="12345", result="X")

    expected_msg = "The supported results are: commit, rollback"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    call = TransactionPostCall(txid="12345", result="commit")
    assert call.endpoint == "/v1/transactions/12345"


def test_method(default_transaction_post_call):
    assert default_transaction_post_call.method == "POST"


def test_parameters(default_transaction_post_call):
    assert default_transaction_post_call.params == {
        "result": "commit",
    }


def test_headers(default_transaction_post_call):
    assert default_transaction_post_call.headers == {
        "Content-Type": "text/plain",
    }


def test_body(default_transaction_post_call):
    assert default_transaction_post_call.body is None


def test_fully_parametrized_call():
    call = TransactionPostCall(txid="12345", result="rollback", database="Documents")
    assert call.method == "POST"
    assert call.endpoint == "/v1/transactions/12345"
    assert call.headers == {
        "Content-Type": "text/plain",
    }
    assert call.params == {
        "result": "rollback",
        "database": "Documents",
    }
    assert call.body is None
