from unittest.mock import MagicMock

from mlclient.api.admin_api import AdminApi
from mlclient.calls.admin import ServerConfigGetCall, TimestampGetCall


def _make_admin_api():
    mock_client = MagicMock()
    return AdminApi(mock_client), mock_client


def test_call_delegates_to_client():
    api, mock_client = _make_admin_api()
    call = TimestampGetCall()
    api.call(call)
    mock_client.call.assert_called_once_with(call)


def test_get_timestamp():
    api, mock_client = _make_admin_api()
    api.get_timestamp()
    args = mock_client.call.call_args
    assert isinstance(args[0][0], TimestampGetCall)


def test_get_server_config():
    api, mock_client = _make_admin_api()
    api.get_server_config()
    args = mock_client.call.call_args
    assert isinstance(args[0][0], ServerConfigGetCall)
