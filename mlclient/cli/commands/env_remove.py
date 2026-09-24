"""The Env Remove Command module.

It exports an implementation for 'env remove' command:
    * EnvRemoveCommand
        Deletes an MLClient environment file.
"""

from __future__ import annotations

from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient.cli.commands._env_common import (
    FILE_PREFIX,
    FILE_SUFFIX,
    resolve_env_dir,
    unknown_env_message,
)
from mlclient.exceptions import WrongParametersError


class EnvRemoveCommand(Command):
    """Deletes an MLClient environment file.

    Resolves .mlclient/mlclient-<name>.yaml the same way ``env show`` does - the
    nearest .mlclient directory in the current directory or its parents, or the
    home directory with ``--global`` - and deletes it after a confirmation
    prompt. ``--force`` skips the prompt, which is also what a non-interactive
    invocation needs since it never confirms.

    Usage:
      env remove [options] [--] <name>

    Arguments:
      name
            The environment name.

    Options:
      -g, --global
            Remove the file in the home directory instead of the current directory
      -f, --force
            Delete without asking for confirmation
    """

    name: str = "env remove"
    description: str = "Deletes an MLClient environment file"
    arguments: list[Argument] = [
        argument("name", "The environment name."),
    ]
    options: list[Option] = [
        option(
            "global",
            "g",
            description=(
                "Remove the file in the home directory instead of the current directory"
            ),
        ),
        option(
            "force",
            "f",
            description="Delete without asking for confirmation",
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
        if not self.option("force") and not self.confirm(
            f"Remove environment <info>{Formatter.escape(name)}</info> "
            f"at <info>{Formatter.escape(str(path))}</info>?",
            default=False,
        ):
            self.line("Aborted.")
            return 0
        path.unlink()
        self.line(f"Removed <info>{Formatter.escape(str(path))}</info>")
        return 0
