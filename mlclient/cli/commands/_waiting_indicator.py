"""A waiting indicator for commands that send a request to one environment.

While the request runs, stderr shows a spinner with the URL and the seconds
waited so far, e.g. ``- Waiting for http://localhost:8002 2.4 s``. It is shown
only when stderr is decorated (a terminal), so redirected output, CI and
scripts never see it, and it is erased before the command prints its result.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from cleo.formatters.formatter import Formatter
from cleo.ui.progress_indicator import ProgressIndicator

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cleo.io.io import IO

_REFRESH_INTERVAL_SECONDS = 0.1
ERASE_LINE = "\r\x1b[2K"


@contextmanager
def waiting_for(
    io: IO,
    url: str,
) -> Iterator[None]:
    """Show a waiting indicator on stderr for the duration of the block.

    Parameters
    ----------
    io : IO
        The command IO; the indicator is written to its error output.
    url : str
        The URL the request is sent to, shown in the indicator.

    Yields
    ------
    None
        Control to the block that sends the request. The indicator line is
        erased when the block ends, also when it raises.
    """
    output = io.error_output
    if not output.is_decorated():
        yield
        return
    indicator = ProgressIndicator(output, fmt="{indicator} {message}", interval=0)
    started = time.perf_counter()
    indicator.start(_waiting_message(url, 0.0))
    stopped = threading.Event()

    def spin() -> None:
        while not stopped.wait(_REFRESH_INTERVAL_SECONDS):
            indicator.set_message(_waiting_message(url, time.perf_counter() - started))
            indicator.advance()

    spinner = threading.Thread(target=spin, daemon=True)
    spinner.start()
    try:
        yield
    finally:
        stopped.set()
        spinner.join()
        output.write(ERASE_LINE)


def _waiting_message(
    url: str,
    waited: float,
) -> str:
    """Describe what the command waits for and how long it has waited.

    Parameters
    ----------
    url : str
        The URL the request is sent to.
    waited : float
        Seconds since the request started.

    Returns
    -------
    str
        The indicator message in cleo markup.
    """
    return f"Waiting for {Formatter.escape(url)} <comment>{waited:.1f} s</comment>"
