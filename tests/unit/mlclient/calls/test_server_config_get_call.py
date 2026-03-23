from mlclient.calls import ApiCall
from mlclient.calls.admin import ServerConfigGetCall


def test_is_api_call():
    assert issubclass(ServerConfigGetCall, ApiCall)


def test_endpoint():
    assert ServerConfigGetCall().endpoint == "/admin/v1/server-config"


def test_method():
    assert ServerConfigGetCall().method == "GET"


def test_parameters():
    assert ServerConfigGetCall().params == {}


def test_headers():
    assert ServerConfigGetCall().headers == {}


def test_body():
    assert ServerConfigGetCall().body is None
