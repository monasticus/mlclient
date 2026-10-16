"""The Version Command module.

It exports an implementation for 'version' command:
    * VersionCommand
        Reports the MarkLogic version of an environment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cleo.commands.command import Command
from cleo.helpers import option
from cleo.io.inputs.option import Option

from mlclient._manager import MLClientManager
from mlclient.cli.commands._multi_env_common import (
    selected_environments,
    time_in_environments,
)
from mlclient.cli.connection import get_async_client, get_client

if TYPE_CHECKING:
    from mlclient.models import MarkLogicVersion


class VersionCommand(Command):
    """Reports the MarkLogic version of an environment.

    Resolves the version through the environment's REST App-Server and prints
    its complete original value, e.g. ``12.0.1`` or ``10.0-9.5``. With several
    environments all are asked at once and a table with one column per
    environment shows each version and how long it took.

    Usage:
      version [options]

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name; repeat it to ask several environments
            (multiple values allowed) [default: ["local"]]
      -c, --connection=CONNECTION
            Connection identifier from the environment or TCP port
    """

    name: str = "version"
    description: str = "Reports the MarkLogic version of an environment"
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name; repeat it to ask several "
            "environments",
            flag=False,
            multiple=True,
            default=["local"],
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
        environments = selected_environments(self)
        if len(environments) > 1:
            return time_in_environments(self, environments, self._fetch_version)
        manager = MLClientManager(environments[0])
        with get_client(manager, self.option("connection")) as ml:
            version = ml.version
        self.line(str(version))
        return 0

    async def _fetch_version(
        self,
        environment: str,
    ) -> MarkLogicVersion:
        """Ask one environment for its MarkLogic version.

        Parameters
        ----------
        environment : str
            The environment name.

        Returns
        -------
        MarkLogicVersion
            The complete MarkLogic version.
        """
        manager = MLClientManager(environment)
        async with get_async_client(manager, self.option("connection")) as ml:
            return await ml.version()
