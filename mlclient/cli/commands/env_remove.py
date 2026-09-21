"""The Env Remove Command module.

It exports an implementation for 'env remove' command:
    * EnvRemoveCommand
        Deletes an MLClient environment file.
"""

from __future__ import annotations

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
        directory = self._env_dir()
        path = directory / f"{_FILE_PREFIX}{name}{_FILE_SUFFIX}"
        if not path.is_file():
            raise WrongParametersError(_unknown_env_message(name, directory))
        if not self.option("force") and not self.confirm(
            f"Remove environment <info>{name}</info> at <info>{path}</info>?",
            default=False,
        ):
            self.line("Aborted.")
            return 0
        path.unlink()
        self.line(f"Removed <info>{path}</info>")
        return 0

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
