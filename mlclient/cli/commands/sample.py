"""Inspect a few XML or JSON nodes from a MarkLogic database."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.io.outputs.output import Type

from mlclient._manager import MLClientManager
from mlclient.cli.commands._multi_env_common import (
    selected_environments,
    time_in_environments,
)
from mlclient.cli.connection import get_async_client, get_client
from mlclient.cli.formatting import prettify
from mlclient.exceptions import WrongParametersError
from mlclient.xquery import cts

if TYPE_CHECKING:
    from mlclient.xquery import XqyExpression

_MAX_SAMPLE_LIMIT = 100


class SampleCommand(Command):
    """Print sample XML or JSON content from the database.

    With several environments all are sampled at once and a table with one
    column per environment shows each sample and how long the search took.

    Usage:
      sample [options] [--] [<path>]

    Arguments:
      path
            Root name or XPath to sample [default: "/"]

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name; repeat it to sample several
            environments (multiple values allowed) [default: ["local"]]
      -c, --connection=CONNECTION
            Connection identifier from the environment or TCP port
      -l, --limit=LIMIT
            Maximum number of sample results (1-100) [default: "1"]
      -j, --json
            Sample JSON documents instead of XML documents
          --no-pretty
            Print sample content without pretty-printing
    """

    name: str = "sample"
    description: str = "Prints sample XML or JSON content from the database"
    arguments: list[Argument] = [
        argument("path", "Root name or XPath to sample", optional=True, default="/"),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name; repeat it to sample "
            "several environments",
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
            "limit",
            "l",
            description="Maximum number of sample results (1-100)",
            flag=False,
            default="1",
        ),
        option(
            "json",
            "j",
            description="Sample JSON documents instead of XML documents",
        ),
        option("no-pretty", description="Print sample content without pretty-printing"),
    ]

    def handle(self) -> int:
        """Search for at most the requested number of nodes and print their content."""
        path = self._get_path()
        limit = self._get_limit()
        options = "format-json" if self.option("json") else "format-xml"
        expression = cts.search(None if path == "/" else path, options=options).pos([1, limit])
        environments = selected_environments(self)
        if len(environments) > 1:
            return self._sample_in_environments(environments, expression)
        manager = MLClientManager(environments[0])
        with get_client(manager, self.option("connection")) as ml:
            results = ml.eval.expression(expression, output_type=str)
        for output in self._format(results):
            self._io.write(output, new_line=True, type=Type.RAW)
        return 0

    def _sample_in_environments(
        self,
        environments: list[str],
        expression: XqyExpression,
    ) -> int:
        """Sample every environment at once and show the samples side by side.

        Parameters
        ----------
        environments : list[str]
            Environment names, one table column each, in the given order.
        expression : XqyExpression
            The search returning the sample nodes.

        Returns
        -------
        int
            0 when every environment returned a sample, 1 when any failed.
        """
        connection = self.option("connection")

        async def search(environment: str) -> list[str] | str:
            manager = MLClientManager(environment)
            async with get_async_client(manager, connection) as ml:
                return await ml.eval.expression(expression, output_type=str)

        def describe(results: list[str] | str) -> str:
            return "\n".join(self._format(results))

        return time_in_environments(self, environments, search, describe)

    def _format(
        self,
        results: list[str] | str,
    ) -> list[str]:
        """Format the sample nodes for printing.

        Parameters
        ----------
        results : list[str] | str
            The serialized nodes returned by the search.

        Returns
        -------
        list[str]
            The nodes, pretty-printed unless --no-pretty was given.
        """
        if isinstance(results, str):
            results = [results]
        if self.option("no-pretty"):
            return results
        content_type = "application/json" if self.option("json") else "application/xml"
        return [prettify(result, content_type) for result in results]

    def _get_path(self) -> str:
        """Resolve a root name to an absolute path, leaving XPath input unchanged.

        Returns
        -------
        str
            Path to search; names without a slash or leading dot gain a slash

        Raises
        ------
        WrongParametersError
            If the supplied root or path is empty
        """
        path = self.argument("path").strip()
        if not path:
            msg = "The sample root or path cannot be empty."
            raise WrongParametersError(msg)
        return path if "/" in path or path.startswith(".") else "/" + path

    def _get_limit(self) -> int:
        """Validate the inclusive upper result position before making a request.

        Returns
        -------
        int
            Maximum number of returned nodes, between 1 and 100 inclusive

        Raises
        ------
        WrongParametersError
            If the limit is not an integer between 1 and 100
        """
        msg = "The sample limit must be an integer between 1 and 100."
        try:
            limit = int(self.option("limit"))
        except ValueError as error:
            raise WrongParametersError(msg) from error
        if not 1 <= limit <= _MAX_SAMPLE_LIMIT:
            raise WrongParametersError(msg)
        return limit
