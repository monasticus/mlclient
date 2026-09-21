"""The Env Edit Command module.

It exports an implementation for 'env edit' command:
    * EnvEditCommand
        Opens an MLClient environment file in the user's editor.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient import _constants as constants
from mlclient.env import find_mlclient_directory
from mlclient.exceptions import MLClientDirectoryNotFoundError, WrongParametersError

_FILE_PREFIX = "mlclient-"
_FILE_SUFFIX = ".yaml"


class EnvEditCommand(Command):
    """Opens an MLClient environment file in the user's editor.

    Resolves .mlclient/mlclient-<name>.yaml the same way ``env show`` does - the
    nearest .mlclient directory in the current directory or its parents, or the
    home directory with ``--global`` - and hands it to the editor named by
    ``$VISUAL`` or ``$EDITOR`` (``vi`` when neither is set). The editor takes over
    the terminal; the command returns its exit status when the editor exits.

    Usage:
      env edit [options] [--] <name>

    Arguments:
      name
            The environment name.

    Options:
      -g, --global
            Edit the file in the home directory instead of the current directory
    """

    name: str = "env edit"
    description: str = "Opens an MLClient environment file in the user's editor"
    arguments: list[Argument] = [
        argument("name", "The environment name."),
    ]
    options: list[Option] = [
        option(
            "global",
            "g",
            description=(
                "Edit the file in the home directory instead of the current directory"
            ),
        ),
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        name = self.argument("name")
        directory = self._env_dir()
        path = directory / f"{_FILE_PREFIX}{name}{_FILE_SUFFIX}"
        if not path.is_file():
            raise WrongParametersError(_unknown_env_message(name, directory))
        editor = _editor()
        self.line(f"Opening <info>{path}</info> in <info>{editor}</info>...")
        return subprocess.call([editor, str(path)])

    def _env_dir(
        self,
    ) -> Path:
        """Locate the .mlclient directory: home when --global, else nearest ancestor."""
        if self.option("global"):
            return Path.home() / constants.ML_CLIENT_DIR
        try:
            return find_mlclient_directory(Path.cwd())
        except MLClientDirectoryNotFoundError:
            return Path.cwd() / constants.ML_CLIENT_DIR


def _editor() -> str:
    """Pick the editor from $VISUAL, then $EDITOR, falling back to vi."""
    return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"


def _env_names(
    directory: Path,
) -> list[str]:
    """List environment names from the .mlclient directory's config files."""
    return sorted(
        path.name.removeprefix(_FILE_PREFIX).removesuffix(_FILE_SUFFIX)
        for path in directory.glob(f"{_FILE_PREFIX}*{_FILE_SUFFIX}")
    )


def _unknown_env_message(
    name: str,
    directory: Path,
) -> str:
    """Report the unknown environment, listing the ones that do exist."""
    names = _env_names(directory)
    available = f" Available: {', '.join(names)}." if names else ""
    return f"No environment [{name}] in {directory}.{available}"
