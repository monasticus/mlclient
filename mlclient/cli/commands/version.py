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


class VersionCommand(Command):
    """Reports the MarkLogic version of an environment.

    Resolves the version through the environment's REST App-Server and prints
    it in dotted form, e.g. ``12.0.1``.

    Usage:
      version [options]

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
      -s, --rest-server=REST-SERVER
            The ML REST Server environmental id
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
            "rest-server",
            "s",
            description="The ML REST Server environmental id",
            flag=False,
        ),
    ]

    def handle(self) -> int:
        """Execute the command."""
        manager = MLClientManager(self.option("environment"))
        with manager.get_client(self.option("rest-server")) as ml:
            version = ml.version
        self.line(".".join(str(part) for part in version))
        return 0
