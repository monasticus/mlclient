"""The ML Client CLI Commands package.

It contains all CLI commands modules:
    * eval
        The Eval Command module.
    * invoke
        The Invoke Command module.
    * logs
        The Logs Command module.
    * http
        The HTTP Command module.
    * sample
        The Sample Command module.
    * env_init
        The Env Init Command module.
    * env_list
        The Env List Command module.
    * env_show
        The Env Show Command module.
    * env_edit
        The Env Edit Command module.
    * env_copy
        The Env Copy Command module.
    * env_remove
        The Env Remove Command module.
    * env_compare
        The Env Compare Command module.
    * health
        The Health Command module.
    * log_level
        The Log Level Command module.
    * version
        The Version Command module.
    * url
        The URL Command module.

It exports the following commands:
    * EvalCommand
        Runs XQuery or JavaScript code.
    * InvokeCommand
        Runs an XQuery or JavaScript module deployed on the server.
    * LogsCommand
        Prints MarkLogic log lines or lists log files.
    * HttpCommand
        Sends a raw HTTP request to any REST endpoint.
    * SampleCommand
        Prints sample XML or JSON content from the database.
    * EnvInitCommand
        Scaffolds an MLClient environment configuration file.
    * EnvListCommand
        Lists MLClient environments.
    * EnvShowCommand
        Renders one MLClient environment's settings.
    * EnvEditCommand
        Opens an MLClient environment file in the user's editor.
    * EnvCopyCommand
        Clones an MLClient environment file under a new name.
    * EnvRemoveCommand
        Deletes an MLClient environment file.
    * EnvCompareCommand
        Compares settings across MLClient environments side by side.
    * HealthCommand
        Reports whether a MarkLogic environment's HealthCheck server is up.
    * LogLevelCommand
        Shows or sets a MarkLogic file/system log level.
    * VersionCommand
        Reports the MarkLogic version of an environment.
    * UrlCommand
        Prints MarkLogic browser URLs for an environment.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from cleo.commands.command import Command

    from mlclient.cli.commands.env_compare import EnvCompareCommand
    from mlclient.cli.commands.env_copy import EnvCopyCommand
    from mlclient.cli.commands.env_edit import EnvEditCommand
    from mlclient.cli.commands.env_init import EnvInitCommand
    from mlclient.cli.commands.env_list import EnvListCommand
    from mlclient.cli.commands.env_remove import EnvRemoveCommand
    from mlclient.cli.commands.env_show import EnvShowCommand
    from mlclient.cli.commands.eval import EvalCommand
    from mlclient.cli.commands.health import HealthCommand
    from mlclient.cli.commands.http import HttpCommand
    from mlclient.cli.commands.invoke import InvokeCommand
    from mlclient.cli.commands.log_level import LogLevelCommand
    from mlclient.cli.commands.logs import LogsCommand
    from mlclient.cli.commands.sample import SampleCommand
    from mlclient.cli.commands.url import UrlCommand
    from mlclient.cli.commands.version import VersionCommand

COMMANDS: dict[str, str] = {
    "logs": "mlclient.cli.commands.logs.LogsCommand",
    "eval": "mlclient.cli.commands.eval.EvalCommand",
    "invoke": "mlclient.cli.commands.invoke.InvokeCommand",
    "http": "mlclient.cli.commands.http.HttpCommand",
    "sample": "mlclient.cli.commands.sample.SampleCommand",
    "env init": "mlclient.cli.commands.env_init.EnvInitCommand",
    "env list": "mlclient.cli.commands.env_list.EnvListCommand",
    "env show": "mlclient.cli.commands.env_show.EnvShowCommand",
    "env edit": "mlclient.cli.commands.env_edit.EnvEditCommand",
    "env copy": "mlclient.cli.commands.env_copy.EnvCopyCommand",
    "env remove": "mlclient.cli.commands.env_remove.EnvRemoveCommand",
    "env compare": "mlclient.cli.commands.env_compare.EnvCompareCommand",
    "health": "mlclient.cli.commands.health.HealthCommand",
    "log-level": "mlclient.cli.commands.log_level.LogLevelCommand",
    "trace-events": "mlclient.cli.commands.trace_events.TraceEventsCommand",
    "url": "mlclient.cli.commands.url.UrlCommand",
    "version": "mlclient.cli.commands.version.VersionCommand",
}

__all__ = [
    "EnvCompareCommand",
    "EnvCopyCommand",
    "EnvEditCommand",
    "EnvInitCommand",
    "EnvListCommand",
    "EnvRemoveCommand",
    "EnvShowCommand",
    "EvalCommand",
    "HealthCommand",
    "HttpCommand",
    "InvokeCommand",
    "LogLevelCommand",
    "LogsCommand",
    "SampleCommand",
    "UrlCommand",
    "VersionCommand",
]


def __getattr__(name: str) -> type[Command]:
    """Resolve an exported command class without importing unrelated commands.

    Parameters
    ----------
    name : str
        Name of a class in the existing package exports.

    Returns
    -------
    type[Command]
        The requested command class, cached as a normal module attribute.

    Raises
    ------
    AttributeError
        If the name is not exported by this package.
    """
    if name in __all__:
        for target in COMMANDS.values():
            module_name, class_name = target.rsplit(".", 1)
            if class_name == name:
                command = cast(
                    "type[Command]", getattr(import_module(module_name), name),
                )
                globals()[name] = command
                return command
    message = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(message)


def __dir__() -> list[str]:
    """List normal attributes and the lazily exported command classes.

    Returns
    -------
    list[str]
        Sorted attribute names, including classes not yet imported.
    """
    return sorted(set(globals()) | set(__all__))
