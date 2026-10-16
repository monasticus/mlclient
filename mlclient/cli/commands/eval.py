"""The Eval Command module.

It exports an implementation for 'eval' command:
    * EvalCommand
        Sends a POST request to the /v1/eval endpoint.
"""

from __future__ import annotations

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient._manager import MLClientManager
from mlclient.cli.commands._execution_common import parse_variables, write_results
from mlclient.cli.commands._multi_env_common import (
    selected_environments,
    time_in_environments,
)
from mlclient.cli.connection import get_async_client, get_client
from mlclient.cli.formatting import prettify
from mlclient.exceptions import WrongParametersError


class EvalCommand(Command):
    """Sends a POST request to the /v1/eval endpoint.

    With several environments the code runs in all of them at once and the
    results are shown in a table with one column per environment, wrapped to fit
    the terminal width. Each column header counts the seconds waited so far and
    shows the final time once that environment answers. Results show up as they
    arrive, cut to the terminal height until every environment has answered.

    Usage:
      eval [options] [--] <code>

    Arguments:
      code
            The code to evaluate (a file path or raw xqy/js code)

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name; repeat it to time the code in several
            environments (multiple values allowed) [default: ["local"]]
      -c, --connection=CONNECTION
            Connection identifier from the environment or TCP port
          --var=VAR
            A variable to be used in the code (multiple values allowed)
      -x, --xquery
            If set, the code will be treated as raw xquery
      -j, --javascript
            If set, the code will be treated as raw javascript
      -d, --database=DATABASE
            Evaluate the code on the named content database
      -t, --txid=TXID
            The transaction identifier of the multi-statement transaction
          --no-pretty
            Print results without reformatting XML or JSON
    """

    name: str = "eval"
    description: str = "Sends a POST request to the /v1/eval endpoint"
    arguments: list[Argument] = [
        argument(
            "code",
            "The code to evaluate (a file path or raw xqy/js code)",
        ),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name; repeat it to time the code "
            "in several environments",
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
            description="A variable to be used in the code",
            flag=False,
        ),
        option(
            "xquery",
            "x",
            description="If set, the code will be treated as raw xquery",
        ),
        option(
            "javascript",
            "j",
            description="If set, the code will be treated as raw javascript",
        ),
        option(
            "database",
            "d",
            description="Evaluate the code on the named content database",
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
        eval_params = self._get_eval_params()
        environments = selected_environments(self)
        if len(environments) > 1:
            return self._time_in_environments(environments, eval_params)
        results = self._call_eval(environments[0], eval_params)
        write_results(self, results)
        return 0

    def _get_eval_params(self):
        """Prepare parameters for an Eval service."""
        code = self.argument("code")
        variables = self.option("var")
        xq_flag = self.option("xquery")
        js_flag = self.option("javascript")
        database = self.option("database")
        txid = self.option("txid")

        if xq_flag and js_flag:
            msg = "You cannot include both the --xquery and the --javascript flag!"
            raise WrongParametersError(msg)

        params = {
            "output_type": str,
            "database": database,
            "txid": txid,
        }
        if xq_flag:
            params["xq"] = code
        if js_flag:
            params["js"] = code
        if not xq_flag and not js_flag:
            params["file"] = code
        if len(variables) > 0:
            params["variables"] = parse_variables(variables)

        return params

    def _time_in_environments(
        self,
        environments: list[str],
        eval_params: dict,
    ) -> int:
        """Evaluate the code in every environment at once and show the results.

        Parameters
        ----------
        environments : list[str]
            Environment names, one table column each, in the given order.
        eval_params : dict
            Keyword arguments for the Eval service.

        Returns
        -------
        int
            0 when every environment returned a result, 1 when any failed.
        """
        connection = self.option("connection")
        pretty = not self.option("no-pretty")

        async def evaluate(environment: str) -> list[str] | str:
            manager = MLClientManager(environment)
            async with get_async_client(manager, connection) as ml:
                return await ml.eval.execute(**eval_params)

        def describe(results: list[str] | str) -> str:
            if pretty:
                results = _prettify(results)
            return "\n".join(results) if isinstance(results, list) else results

        return time_in_environments(self, environments, evaluate, describe)

    def _call_eval(
        self,
        environment: str,
        eval_params: dict,
    ):
        """Evaluate the code and get results."""
        rest_server = self.option("connection")

        mgr = MLClientManager(environment)
        with get_client(mgr, rest_server) as ml:
            self.info(f"Evaluating code using REST App-Server {ml.http.base_url}")
            return ml.eval.execute(**eval_params)


def _prettify(
    results: list[str] | str,
) -> list[str] | str:
    """Reformat XML and JSON results, item by item for a sequence.

    Parameters
    ----------
    results : list[str] | str
        Results returned by the Eval service.

    Returns
    -------
    list[str] | str
        The results in the same shape, XML and JSON reformatted.
    """
    if isinstance(results, list):
        return [prettify(item) for item in results]
    return prettify(results)
