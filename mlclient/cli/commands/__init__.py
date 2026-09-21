"""The ML Client CLI Commands package.

It contains all CLI commands modules:
    * eval
        The Eval Command module.
    * logs
        The Logs Command module.
    * http
        The HTTP Command module.
    * env_init
        The Env Init Command module.
    * env_show
        The Env Show Command module.
    * env_edit
        The Env Edit Command module.
    * health
        The Health Command module.
    * log_level
        The Log Level Command module.
    * version
        The Version Command module.

It exports the following commands:
    * EvalCommand
        Sends a GET request to the /v1/eval endpoint.
    * LogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
    * HttpCommand
        Sends a raw HTTP request to any REST endpoint.
    * EnvInitCommand
        Scaffolds an MLClient environment configuration file.
    * EnvShowCommand
        Lists MLClient environments, or renders one environment's settings.
    * EnvEditCommand
        Opens an MLClient environment file in the user's editor.
    * HealthCommand
        Reports whether a MarkLogic environment's HealthCheck server is up.
    * LogLevelCommand
        Shows or sets a MarkLogic file/system log level.
    * VersionCommand
        Reports the MarkLogic version of an environment.
"""

from mlclient.cli.commands.env_edit import EnvEditCommand
from mlclient.cli.commands.env_init import EnvInitCommand
from mlclient.cli.commands.env_show import EnvShowCommand
from mlclient.cli.commands.eval import EvalCommand
from mlclient.cli.commands.health import HealthCommand
from mlclient.cli.commands.http import HttpCommand
from mlclient.cli.commands.log_level import LogLevelCommand
from mlclient.cli.commands.logs import LogsCommand
from mlclient.cli.commands.version import VersionCommand

__all__ = [
    "EnvEditCommand",
    "EnvInitCommand",
    "EnvShowCommand",
    "EvalCommand",
    "HealthCommand",
    "HttpCommand",
    "LogLevelCommand",
    "LogsCommand",
    "VersionCommand",
]
