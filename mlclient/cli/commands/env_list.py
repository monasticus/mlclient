"""The Env List Command module.

It exports an implementation for 'env list' command:
    * EnvListCommand
        Lists MLClient environments.
"""

from __future__ import annotations

from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import option
from cleo.io.inputs.option import Option

from mlclient.cli.commands._env_common import (
    announce_source,
    env_names,
    resolve_env_dir,
)


class EnvListCommand(Command):
    """Command listing the environments of a .mlclient directory.

    Prints one environment name per line, sorted. ``--global`` reads the home
    directory instead of the current one.

    Usage:
      env list [options]

    Options:
      -g, --global
            Read from the home directory instead of the current directory
    """

    name: str = "env list"
    description: str = "Lists MLClient environments"
    options: list[Option] = [
        option(
            "global",
            "g",
            description="Read from the home directory instead of the current directory",
        ),
    ]

    def handle(
        self,
    ) -> int:
        """Print the environment names found in the .mlclient directory."""
        directory = resolve_env_dir(self)
        names = env_names(directory)
        if not names:
            directory_name = Formatter.escape(str(directory))
            self.line(f"No environments found in <info>{directory_name}</info>")
            return 0
        announce_source(self, directory, directory)
        for name in names:
            self.line(Formatter.escape(name))
        return 0
