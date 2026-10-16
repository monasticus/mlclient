"""Shared building blocks for the ``eval`` and ``invoke`` commands.

Both run code on MarkLogic, bind ``--var`` options as external variables and
print the results the same way. They live here so neither command reaches
into the other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cleo.io.outputs.output import Type

from mlclient.cli.formatting import prettify
from mlclient.exceptions import WrongParametersError

if TYPE_CHECKING:
    from cleo.commands.command import Command


def parse_variables(
    options: list[str],
) -> dict[str, str]:
    """Turn repeated ``--var name=value`` options into external variables.

    Parameters
    ----------
    options : list[str]
        The ``--var`` option values. Only the first ``=`` separates the name
        from the value, so a value may itself contain ``=``.

    Returns
    -------
    dict[str, str]
        External variables keyed by name, with string values.

    Raises
    ------
    WrongParametersError
        If an option has no ``=`` separating a name from its value.
    """
    variables = {}
    for option in options:
        name, separator, value = option.partition("=")
        if not separator:
            msg = f"A variable must be passed as name=value, got: {option}"
            raise WrongParametersError(msg)
        variables[name] = value
    return variables


def write_results(
    command: Command,
    results: str | list[str],
) -> None:
    """Print results, formatting XML and JSON unless ``--no-pretty`` is set.

    Parameters
    ----------
    command : Command
        The running command; its ``--no-pretty`` option and output are used.
    results : str | list[str]
        One raw result, or a list of them, each printed on its own line.
    """
    if not command.option("no-pretty"):
        results = (
            [prettify(item) for item in results]
            if isinstance(results, list)
            else prettify(results)
        )

    command.io.write("\n")
    command.io.write(results, new_line=True, type=Type.RAW)
