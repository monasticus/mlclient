"""Editor launching shared by environment editing and copying."""

from __future__ import annotations

import os
import shlex
import subprocess
from typing import TYPE_CHECKING

from cleo.formatters.formatter import Formatter

from mlclient.exceptions import WrongParametersError

if TYPE_CHECKING:
    from pathlib import Path

    from cleo.commands.command import Command


def open_in_editor(command: Command, path: Path) -> int:
    """Launch the user's editor, inheriting the terminal without invoking a shell.

    Parameters
    ----------
    command : Command
        CLI command that reports which file and editor will be opened.
    path : Path
        Existing environment file to edit.

    Returns
    -------
    int
        The editor's exit status.

    Raises
    ------
    WrongParametersError
        If the editor setting is empty or has invalid quoting.
    OSError
        If the editor executable cannot be started.
    """
    editor = _editor()
    try:
        arguments = shlex.split(editor)
    except ValueError:
        arguments = []
    if not arguments:
        message = "Set VISUAL or EDITOR to a valid executable and optional arguments."
        raise WrongParametersError(message)
    command.line(
        f"Opening <info>{Formatter.escape(str(path))}</info> "
        f"in <info>{Formatter.escape(editor)}</info>...",
    )
    return subprocess.call([*arguments, str(path)])


def _editor() -> str:
    """Pick VISUAL, then EDITOR, using vi when both are unset or empty."""
    return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
