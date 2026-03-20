from mlclient.calls import ApiCall
from mlclient.calls.admin import ServerConfigGetCall, TimestampGetCall


def test_timestamp_get_call_is_api_call():
    assert issubclass(TimestampGetCall, ApiCall)


def test_timestamp_get_call_endpoint():
    assert TimestampGetCall().endpoint == "/admin/v1/timestamp"


def test_timestamp_get_call_default_method():
    assert TimestampGetCall().method == "GET"


def test_server_config_get_call_is_api_call():
    assert issubclass(ServerConfigGetCall, ApiCall)


def test_server_config_get_call_endpoint():
    assert ServerConfigGetCall().endpoint == "/admin/v1/server-config"


def test_server_config_get_call_default_method():
    assert ServerConfigGetCall().method == "GET"
