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
from mlclient.cli.commands._execution_common import parse_variables, write_results
from mlclient.cli.connection import get_client


class InvokeCommand(Command):
    """Sends a POST request to the /v1/invoke endpoint.

    Usage:
      invoke [options] [--] <module>

    Arguments:
      module
            The path of a module installed in MarkLogic

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
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
        results = self._invoke_module(variables)
        write_results(self, results)
        return 0

    def _invoke_module(
        self,
        variables: dict[str, str],
    ):
        """Invoke the module and get its results.

        Parameters
        ----------
        variables : dict[str, str]
            External variables to pass to the module.

        Returns
        -------
        str | list[str]
            The raw module results.
        """
        env = self.option("environment")
        rest_server = self.option("connection")

        mgr = MLClientManager(env)
        with get_client(mgr, rest_server) as ml:
            self.info(f"Invoking module using REST App-Server {ml.http.base_url}")
            return ml.invoke.module(
                self.argument("module"),
                variables=variables,
                database=self.option("database"),
                txid=self.option("txid"),
                output_type=str,
            )
