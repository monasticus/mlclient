import pytest

from mlclient.clients import LogType
from mlclient.exceptions import InvalidLogTypeError


def test_get_error_log_type():
    assert LogType.get("error") == LogType.ERROR


def test_get_access_log_type():
    assert LogType.get("access") == LogType.ACCESS


def test_get_request_log_type():
    assert LogType.get("request") == LogType.REQUEST


def test_get_invalid_log_type():
    with pytest.raises(InvalidLogTypeError) as err:
        LogType.get("invalid")

    expected_msg = "Invalid log type! Allowed values are: error, access, request."
    assert err.value.args[0] == expected_msg
