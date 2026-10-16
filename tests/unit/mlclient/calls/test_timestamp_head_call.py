from mlclient.calls import ApiCall, TimestampHeadCall


def test_is_api_call():
    assert issubclass(TimestampHeadCall, ApiCall)


def test_endpoint():
    assert TimestampHeadCall().endpoint == "/admin/v1/timestamp"


def test_method():
    assert TimestampHeadCall().method == "HEAD"


def test_parameters():
    assert TimestampHeadCall().params == {}


def test_headers():
    assert TimestampHeadCall().headers == {}


def test_body():
    assert TimestampHeadCall().body is None
