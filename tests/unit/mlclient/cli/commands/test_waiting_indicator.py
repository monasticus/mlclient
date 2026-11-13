from __future__ import annotations

import time

import pytest
from cleo.io.buffered_io import BufferedIO
from cleo.io.outputs.output import Verbosity

from mlclient.cli.commands._waiting_indicator import ERASE_LINE, waiting_for

URL = "http://localhost:8002"


def test_waiting_for_shows_the_url_on_a_decorated_stderr():
    io = BufferedIO(decorated=True)

    with waiting_for(io, URL):
        pass

    error = io.fetch_error()
    assert f"Waiting for {URL}" in error
    assert io.fetch_output() == ""


def test_waiting_for_erases_its_line_when_the_block_ends():
    io = BufferedIO(decorated=True)

    with waiting_for(io, URL):
        pass

    assert io.fetch_error().endswith(ERASE_LINE)


def test_waiting_for_erases_its_line_when_the_block_raises():
    io = BufferedIO(decorated=True)

    with pytest.raises(RuntimeError), waiting_for(io, URL):
        raise RuntimeError

    assert io.fetch_error().endswith(ERASE_LINE)


def test_waiting_for_counts_the_seconds_waited():
    io = BufferedIO(decorated=True)

    with waiting_for(io, URL):
        time.sleep(0.25)

    error = io.fetch_error()
    assert "0.0 s" in error
    assert "0.1 s" in error or "0.2 s" in error


def test_waiting_for_shows_nothing_when_stderr_is_not_a_terminal():
    io = BufferedIO(decorated=False)

    with waiting_for(io, URL):
        time.sleep(0.15)

    assert io.fetch_error() == ""
    assert io.fetch_output() == ""


def test_waiting_for_shows_nothing_in_quiet_mode():
    io = BufferedIO(decorated=True)
    io.set_verbosity(Verbosity.QUIET)

    with waiting_for(io, URL):
        time.sleep(0.15)

    assert io.fetch_error() == ""
