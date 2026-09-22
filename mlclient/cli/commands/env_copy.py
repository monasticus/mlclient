"""The Env Copy Command module.

It exports an implementation for 'env copy' command:
    * EnvCopyCommand
        Clones an MLClient environment file under a new name.
"""

from __future__ import annotations

import shutil
import stat
import tempfile
from pathlib import Path

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
from mlclient.cli.commands._env_editor import open_in_editor
from mlclient.exceptions import EnvironmentFileExistsError, WrongParametersError


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
        directory = resolve_env_dir(self)
        source_path = directory / f"{FILE_PREFIX}{source}{FILE_SUFFIX}"
        if not source_path.is_file():
            raise WrongParametersError(unknown_env_message(source, directory))
        target_path = directory / f"{FILE_PREFIX}{target}{FILE_SUFFIX}"
        _copy_environment(source_path, target_path, force=self.option("force"))
        self.line(
            f"Copied <info>{Formatter.escape(source)}</info> "
            f"to <info>{Formatter.escape(target_path.as_posix())}</info>",
        )
        if self.option("edit"):
            return open_in_editor(self, target_path)
        return 0


def _copy_environment(source: Path, target: Path, *, force: bool) -> None:
    """Publish a complete byte-for-byte copy without broadening permissions.

    Parameters
    ----------
    source : Path
        Existing configuration to copy.
    target : Path
        Destination in the same environment directory.
    force : bool
        Replace an existing target atomically. Its permissions are retained
        when stricter than the source permissions.

    Raises
    ------
    EnvironmentFileExistsError
        If a target already exists and force is false.
    OSError
        If reading, writing or publishing fails. An existing target is preserved.
    """
    mode = stat.S_IMODE(source.stat().st_mode)
    if force and target.exists():
        mode &= stat.S_IMODE(target.stat().st_mode)
    with tempfile.TemporaryDirectory(
        dir=target.parent,
        prefix=".mlclient-copy-",
    ) as scratch:
        pending = Path(scratch) / target.name
        shutil.copyfile(source, pending)
        pending.chmod(mode)
        if force:
            pending.replace(target)
        else:
            try:
                target.hardlink_to(pending)
            except FileExistsError:
                raise EnvironmentFileExistsError(
                    Formatter.escape(target.as_posix()),
                ) from None
