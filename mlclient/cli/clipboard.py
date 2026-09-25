"""Copy text to the platform clipboard.

It exports a single function:

    * copy_to_clipboard
        Send text to the operating system's clipboard tool.
"""

from __future__ import annotations

import os
import subprocess
import sys


def copy_to_clipboard(text: str) -> None:
    """Send text through stdin to the platform's clipboard tool.

    Selects ``clip`` on Windows, ``pbcopy`` on macOS, ``wl-copy`` under a
    Wayland session and ``xclip`` otherwise.

    Parameters
    ----------
    text : str
        The text to place on the clipboard.

    Raises
    ------
    OSError
        If the clipboard tool is missing or cannot be launched.
    subprocess.SubprocessError
        If the clipboard tool exits with an error or times out.
    """
    encoding = "utf-8"
    if sys.platform == "win32":
        command = ["clip"]
        encoding = "utf-16"
    elif sys.platform == "darwin":
        command = ["pbcopy"]
    elif os.environ.get("WAYLAND_DISPLAY"):
        command = ["wl-copy"]
    else:
        command = ["xclip", "-selection", "clipboard"]
    subprocess.run(
        command,
        input=text.encode(encoding),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
