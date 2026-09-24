"""The Env Edit Command module.

It exports an implementation for 'env edit' command:
    * EnvEditCommand
        Opens an MLClient environment file in the user's editor.
"""

from __future__ import annotations

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient.cli.commands._env_common import (
    FILE_PREFIX,
    FILE_SUFFIX,
    resolve_env_dir,
    unknown_env_message,
)
from mlclient.cli.commands._env_editor import open_in_editor
from mlclient.exceptions import WrongParametersError


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
        directory = resolve_env_dir(self)
        path = directory / f"{FILE_PREFIX}{name}{FILE_SUFFIX}"
        if not path.is_file():
            raise WrongParametersError(unknown_env_message(name, directory))
        return open_in_editor(self, path)
