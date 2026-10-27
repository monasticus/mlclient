"""The Invoke Command module.

It exports an implementation for 'invoke' command:
    * InvokeCommand
        Sends a POST request to the /v1/invoke endpoint.
"""

from __future__ import annotations

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient._manager import MLClientManager
from mlclient.cli.commands._execution_common import (
    format_results,
    parse_variables,
    write_results,
)
from mlclient.cli.commands._multi_env_common import (
    selected_environments,
    time_in_environments,
)
from mlclient.cli.connection import get_async_client, get_client


class InvokeCommand(Command):
    """Sends a POST request to the /v1/invoke endpoint.

    Usage:
      invoke [options] [--] <module>

    Arguments:
      module
            The path of a module installed in MarkLogic

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment names; repeat to compare (default: local)
      -c, --connection=CONNECTION
            Connection identifier from the environment or TCP port
          --var=VAR
            A variable to be used in the module (multiple values allowed)
      -d, --database=DATABASE
            Invoke the module on the named content database
      -t, --txid=TXID
            The transaction identifier of the multi-statement transaction
          --no-pretty
            Print results without reformatting XML or JSON
    """

    name: str = "invoke"
    description: str = "Sends a POST request to the /v1/invoke endpoint"
    arguments: list[Argument] = [
        argument(
            "module",
            "The path of a module installed in MarkLogic",
        ),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name; repeat to compare "
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
        option(
            "var",
            multiple=True,
            description="A variable to be used in the module",
            flag=False,
        ),
        option(
            "database",
            "d",
            description="Invoke the module on the named content database",
            flag=False,
        ),
        option(
            "txid",
            "t",
            description="The transaction identifier of the multi-statement transaction",
            flag=False,
        ),
        option(
            "no-pretty",
            description="Print results without reformatting XML or JSON",
        ),
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        variables = parse_variables(self.option("var"))
        environments = selected_environments(self)
        if len(environments) > 1:
            return self._time_in_environments(environments, variables)
        results = self._invoke_module(environments[0], variables)
        write_results(self, results)
        return 0

    def _invoke_module(
        self,
        environment: str,
        variables: dict[str, str],
    ):
        """Invoke the module and get its results.

        Parameters
        ----------
        environment : str
            Environment in which to invoke the module.
        variables : dict[str, str]
            External variables to pass to the module.

        Returns
        -------
        str | list[str]
            The raw module results.
        """
        rest_server = self.option("connection")

        mgr = MLClientManager(environment)
        with get_client(mgr, rest_server) as ml:
            self.info(f"Invoking module using REST App-Server {ml.http.base_url}")
            return ml.invoke.module(
                self.argument("module"),
                variables=variables,
                database=self.option("database"),
                txid=self.option("txid"),
                output_type=str,
            )

    def _time_in_environments(
        self,
        environments: list[str],
        variables: dict[str, str],
    ) -> int:
        """Invoke the module concurrently and compare the results.

        Parameters
        ----------
        environments : list[str]
            Environments in display order.
        variables : dict[str, str]
            External variables passed to every invocation.

        Returns
        -------
        int
            Zero when every invocation succeeds, one if any fails.
        """
        connection = self.option("connection")
        pretty = not self.option("no-pretty")

        async def invoke(environment: str) -> str | list[str]:
            manager = MLClientManager(environment)
            async with get_async_client(manager, connection) as ml:
                return await ml.invoke.module(
                    self.argument("module"),
                    variables=variables,
                    database=self.option("database"),
                    txid=self.option("txid"),
                    output_type=str,
                )

        def describe(results: str | list[str]) -> str:
            results = format_results(results, pretty=pretty)
            return "\n".join(results) if isinstance(results, list) else results

        return time_in_environments(self, environments, invoke, describe)
