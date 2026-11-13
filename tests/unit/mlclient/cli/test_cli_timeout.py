from __future__ import annotations

import httpx
import pytest

from mlclient._options import UNSET
from mlclient.cli.timeout import parse_timeout, timed_out_message
from mlclient.exceptions import WrongParametersError

# --- parse_timeout ---


def test_parse_timeout_keeps_the_client_default_when_absent():
    assert parse_timeout(None) is UNSET


@pytest.mark.parametrize(("value", "seconds"), [("2", 2.0), ("0.5", 0.5)])
def test_parse_timeout_reads_seconds(value, seconds):
    assert parse_timeout(value) == seconds


def test_parse_timeout_zero_disables_the_timeout():
    assert parse_timeout("0") is None


@pytest.mark.parametrize("value", ["abc", "", "-1", "nan", "inf"])
def test_parse_timeout_rejects_anything_but_finite_non_negative_seconds(value):
    expected = f"--timeout must be a non-negative number of seconds, got: {value!r}"

    with pytest.raises(WrongParametersError, match="non-negative") as error:
        parse_timeout(value)

    assert str(error.value) == expected


# --- timed_out_message ---


@pytest.mark.parametrize(
    ("error_type", "seconds"),
    [
        (httpx.ConnectTimeout, "1"),
        (httpx.ReadTimeout, "60"),
        (httpx.WriteTimeout, "2.5"),
        (httpx.PoolTimeout, "4"),
    ],
)
def test_timed_out_message_names_the_expired_component(error_type, seconds):
    timeout = httpx.Timeout(connect=1, read=60, write=2.5, pool=4)
    request = httpx.Request(
        "POST",
        "http://localhost:8000/v1/eval",
        extensions={"timeout": timeout.as_dict()},
    )

    message = timed_out_message(error_type("timed out", request=request))

    assert message == (
        f"Request timed out after {seconds}s - it may still be running on the server"
    )
