import pytest

from mlclient import exceptions
from mlclient.calls import TransactionGetCall


@pytest.fixture
def default_transaction_get_call():
    """Returns a TransactionGetCall instance"""
    return TransactionGetCall(txid="12345")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        TransactionGetCall(txid="12345", data_format="text")

    expected_msg = "The supported formats are: xml, json"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    assert TransactionGetCall(txid="12345").endpoint == "/v1/transactions/12345"


def test_method(default_transaction_get_call):
    assert default_transaction_get_call.method == "GET"


def test_parameters(default_transaction_get_call):
    assert default_transaction_get_call.params == {
        "format": "xml",
    }


def test_headers(default_transaction_get_call):
    assert default_transaction_get_call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_none_format():
    call = TransactionGetCall(txid="12345", data_format=None)
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_xml_format():
    call = TransactionGetCall(txid="12345", data_format="xml")
    assert call.headers == {
        "Accept": "application/xml",
    }


def test_headers_for_json_format():
    call = TransactionGetCall(txid="12345", data_format="json")
    assert call.headers == {
        "Accept": "application/json",
    }


def test_body(default_transaction_get_call):
    assert default_transaction_get_call.body is None


def test_fully_parametrized_call():
    call = TransactionGetCall(txid="12345", data_format="json", database="Documents")
    assert call.method == "GET"
    assert call.endpoint == "/v1/transactions/12345"
    assert call.headers == {
        "Accept": "application/json",
    }
    assert call.params == {
        "format": "json",
        "database": "Documents",
    }
    assert call.body is None
