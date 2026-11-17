"""A waiting indicator for commands that send a request to one environment.

While the request runs, stderr shows a spinner with the URL and the seconds
waited so far, e.g. ``●·· Request to http://localhost:8002 2.4 s``. It is shown
only when stderr is decorated (a terminal), so redirected output, CI and
scripts never see it. When waiting ends, the line shows the elapsed time
before the command prints its result or reports an error.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from cleo.formatters.formatter import Formatter
from cleo.ui.progress_indicator import ProgressIndicator

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from cleo.io.io import IO

_REFRESH_INTERVAL_SECONDS = 0.15
ERASE_LINE = "\r\x1b[2K"


@contextmanager
def waiting_for(
    io: IO,
    url: str,
    *,
    progress: Callable[[], str] | None = None,
) -> Iterator[None]:
    """Show a waiting indicator on stderr for the duration of the block.

    Parameters
    ----------
    io : IO
        The command IO; the indicator is written to its error output.
    url : str
        The URL the request is sent to, shown in the indicator.
    progress : Callable[[], str] | None
        Optional live progress text, read without performing I/O.

    Yields
    ------
    None
        Control to the block that sends the request. The indicator line is
        replaced with the elapsed time when the block ends, also when it raises.
    """
    output = io.error_output
    if not output.is_decorated():
        yield
        return
    indicator = ProgressIndicator(
        output,
        fmt="<fg=blue>{indicator} {message}</>",
        interval=0,
        values=["●··", "·●·", "··●", "·●·"],
    )
    started = time.perf_counter()
    indicator.start(f"{_request_message(url, progress)} 0.0 s")
    stopped = threading.Event()

    def spin() -> None:
        while not stopped.wait(_REFRESH_INTERVAL_SECONDS):
            indicator.set_message(
                f"{_request_message(url, progress)} "
                f"{time.perf_counter() - started:.1f} s",
            )
            indicator.advance()

    spinner = threading.Thread(target=spin, daemon=True)
    spinner.start()
    try:
        yield
    finally:
        stopped.set()
        spinner.join()
        elapsed = time.perf_counter() - started
        output.write(ERASE_LINE)
        output.write_line(
            f"<fg=blue>    {_request_message(url, progress)} "
            f"Elapsed: {elapsed:.3f} s</>",
        )


def _request_message(
    url: str,
    progress: Callable[[], str] | None,
) -> str:
    """Build the stable request label for animation and completion.

    Parameters
    ----------
    url : str
        The request URL.
    progress : Callable[[], str] | None
        Optional progress text provider, called from the animation thread.

    Returns
    -------
    str
        The URL and progress escaped for Cleo markup.
    """
    detail = f" {Formatter.escape(progress())}" if progress else ""
    return f"Request to {Formatter.escape(url)}{detail}"
