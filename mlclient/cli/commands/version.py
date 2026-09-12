"""The Version Command module.

It exports an implementation for 'version' command:
    * VersionCommand
        Reports the MarkLogic version of an environment.
"""

from __future__ import annotations

from cleo.commands.command import Command
from cleo.helpers import option
from cleo.io.inputs.option import Option

from mlclient import MLClientManager
from mlclient.cli.connection import get_client


class VersionCommand(Command):
    """Reports the MarkLogic version of an environment.

    Resolves the version through the environment's REST App-Server and prints
    its complete original value, e.g. ``12.0.1`` or ``10.0-9.5``.

    Usage:
      version [options]

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
      -c, --connection=CONNECTION
            Connection identifier from the environment or TCP port
    """

    name: str = "version"
    description: str = "Reports the MarkLogic version of an environment"
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
        ),
        option(
            "connection",
            "c",
            description="Connection identifier from the environment or TCP port",
            flag=False,
        ),
    ]

    def handle(self) -> int:
        """Execute the command."""
        manager = MLClientManager(self.option("environment"))
        with get_client(manager, self.option("connection")) as ml:
            version = ml.version
        self.line(str(version))
        return 0
