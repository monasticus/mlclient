"""The ML Client CLI Commands package.

It contains all CLI commands modules:
    * eval
        The Eval Command module.
    * logs
        The Logs Command module.
    * env_init
        The Env Init Command module.
    * env_show
        The Env Show Command module.
    * health
        The Health Command module.
    * version
        The Version Command module.

It exports the following commands:
    * EvalCommand
        Sends a GET request to the /v1/eval endpoint.
    * LogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
    * EnvInitCommand
        Scaffolds an MLClient environment configuration file.
    * EnvShowCommand
        Lists MLClient environments, or renders one environment's settings.
    * HealthCommand
        Reports whether a MarkLogic environment's HealthCheck server is up.
    * VersionCommand
        Reports the MarkLogic version of an environment.
"""

from .env_init import EnvInitCommand
from .env_show import EnvShowCommand
from .eval import EvalCommand
from .health import HealthCommand
from .logs import LogsCommand
from .version import VersionCommand

__all__ = [
    "EnvInitCommand",
    "EnvShowCommand",
    "EvalCommand",
    "HealthCommand",
    "LogsCommand",
    "VersionCommand",
]
