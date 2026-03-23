from mlclient.calls import ApiCall
from mlclient.calls.admin import TimestampGetCall


def test_is_api_call():
    assert issubclass(TimestampGetCall, ApiCall)


def test_endpoint():
    assert TimestampGetCall().endpoint == "/admin/v1/timestamp"


def test_method():
    assert TimestampGetCall().method == "GET"


def test_parameters():
    assert TimestampGetCall().params == {}


def test_headers():
    assert TimestampGetCall().headers == {}


def test_body():
    assert TimestampGetCall().body is None
