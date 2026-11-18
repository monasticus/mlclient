"""Shared option definitions for MLClient CLI commands."""

from __future__ import annotations

from cleo.helpers import option
from cleo.io.inputs.option import Option


def environment_option(
    *,
    description: str = "The ML Client environment name",
    multiple: bool = False,
) -> Option:
    """Define the ``-e/--environment`` selector.

    Parameters
    ----------
    description : str
        Command-specific help text.
    multiple : bool
        Whether to accept repeated environments and return a list of names.

    Returns
    -------
    Option
        A selector defaulting to local, as a name or a list of names.
    """
    return option(
        "environment",
        "e",
        description=description,
        flag=False,
        multiple=multiple,
        default=["local"] if multiple else "local",
    )


def connection_option() -> Option:
    """Define the ``-c/--connection`` selector.

    Returns
    -------
    Option
        A configured connection identifier or TCP port, with no default override.
    """
    return option(
        "connection",
        "c",
        description="Connection identifier from the environment or TCP port",
        flag=False,
    )


def database_option(description: str) -> Option:
    """Define the ``-d/--database`` selector.

    Parameters
    ----------
    description : str
        Command-specific help text.

    Returns
    -------
    Option
        A database name, leaving the connection's database unchanged when absent.
    """
    return option("database", "d", description=description, flag=False)


def variable_option(description: str) -> Option:
    """Define the repeatable ``--var`` option.

    Parameters
    ----------
    description : str
        Command-specific help text.

    Returns
    -------
    Option
        The external variables supplied to the evaluated code or module.
    """
    return option("var", description=description, flag=False, multiple=True)


def transaction_id_option() -> Option:
    """Define the ``-t/--txid`` option.

    Returns
    -------
    Option
        The transaction identifier, with no implicit transaction.
    """
    return option(
        "txid",
        "t",
        description="The transaction identifier of the multi-statement transaction",
        flag=False,
    )


def no_pretty_option(
    description: str = "Print results without reformatting XML or JSON",
) -> Option:
    """Define the ``--no-pretty`` flag.

    Parameters
    ----------
    description : str
        Command-specific help text.

    Returns
    -------
    Option
        A flag disabling result formatting when present.
    """
    return option("no-pretty", description=description)


def timeout_option() -> Option:
    """Define the ``--timeout SECONDS`` option.

    Returns
    -------
    Option
        A value option read with :func:`mlclient.cli.timeout.parse_timeout`.
    """
    return option(
        "timeout",
        description="Seconds to wait for MarkLogic, 0 waits indefinitely "
        "(default: connect 5, read 60); a timed-out request may still run on "
        "the server and an update may still commit",
        flag=False,
    )
