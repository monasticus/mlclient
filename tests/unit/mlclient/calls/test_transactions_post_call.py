import pytest

from mlclient.calls import TransactionsPostCall


@pytest.fixture
def default_transactions_post_call():
    """Returns a TransactionsPostCall instance"""
    return TransactionsPostCall()


def test_endpoint(default_transactions_post_call):
    assert default_transactions_post_call.endpoint == "/v1/transactions"


def test_method(default_transactions_post_call):
    assert default_transactions_post_call.method == "POST"


def test_parameters(default_transactions_post_call):
    assert default_transactions_post_call.params == {}


def test_headers(default_transactions_post_call):
    assert default_transactions_post_call.headers == {
        "Content-Type": "text/plain",
    }


def test_body(default_transactions_post_call):
    assert default_transactions_post_call.body is None


def test_fully_parametrized_call():
    call = TransactionsPostCall(
        name="my-txn",
        time_limit=60,
        database="Documents",
    )
    assert call.method == "POST"
    assert call.endpoint == "/v1/transactions"
    assert call.headers == {
        "Content-Type": "text/plain",
    }
    assert call.params == {
        "name": "my-txn",
        "timeLimit": 60,
        "database": "Documents",
    }
    assert call.body is None
