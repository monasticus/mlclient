"""The Env Copy Command module.

It exports an implementation for 'env copy' command:
    * EnvCopyCommand
        Clones an MLClient environment file under a new name.
"""

from __future__ import annotations

from pathlib import Path

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient import _constants as constants
from mlclient.cli.commands.env_edit import open_in_editor
from mlclient.env import find_mlclient_directory
from mlclient.exceptions import (
    EnvironmentFileExistsError,
    MLClientDirectoryNotFoundError,
    WrongParametersError,
)

_FILE_PREFIX = "mlclient-"
_FILE_SUFFIX = ".yaml"


class EnvCopyCommand(Command):
    """Clones an MLClient environment file under a new name.

    Resolves the source .mlclient/mlclient-<source>.yaml the same way ``env show``
    does - the nearest .mlclient directory in the current directory or its
    parents, or the home directory with ``--global`` - and writes it verbatim to
    mlclient-<target>.yaml beside it, preserving comments. Refuses to overwrite an
    existing target unless ``--force``; ``--edit`` opens the copy afterwards.

    Usage:
      env copy [options] [--] <source> <target>

    Arguments:
      source
            The environment name to copy from.
      target
            The environment name to copy to.

    Options:
      -g, --global
            Copy within the home directory instead of the current directory
      -f, --force
            Overwrite the target when it already exists
      -e, --edit
            Open the copy in your editor after copying
    """

    name: str = "env copy"
    description: str = "Clones an MLClient environment file under a new name"
    arguments: list[Argument] = [
        argument("source", "The environment name to copy from."),
        argument("target", "The environment name to copy to."),
    ]
    options: list[Option] = [
        option(
            "global",
            "g",
            description=(
                "Copy within the home directory instead of the current directory"
            ),
        ),
        option(
            "force",
            "f",
            description="Overwrite the target when it already exists",
        ),
        option(
            "edit",
            "e",
            description="Open the copy in your editor after copying",
        ),
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        source = self.argument("source")
        target = self.argument("target")
        directory = self._env_dir()
        source_path = directory / f"{_FILE_PREFIX}{source}{_FILE_SUFFIX}"
        if not source_path.is_file():
            raise WrongParametersError(_unknown_env_message(source, directory))
        target_path = directory / f"{_FILE_PREFIX}{target}{_FILE_SUFFIX}"
        if target_path.exists() and not self.option("force"):
            raise EnvironmentFileExistsError(target_path.as_posix())
        target_path.write_text(source_path.read_text())
        self.line(
            f"Copied <info>{source}</info> to <info>{target_path.as_posix()}</info>",
        )
        if self.option("edit"):
            return open_in_editor(self, target_path)
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
