"""The ML Client CLI Commands package.

It contains all CLI commands modules:
    * call_eval
        The Call Eval Command module.
    * call_logs
        The Call Logs Command module.
    * env_init
        The Env Init Command module.
    * env_show
        The Env Show Command module.
    * health
        The Health Command module.
    * version
        The Version Command module.

It exports the following commands:
    * CallEvalCommand
        Sends a GET request to the /v1/eval endpoint.
    * CallLogsCommand
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

from .call_eval import CallEvalCommand
from .call_logs import CallLogsCommand
from .env_init import EnvInitCommand
from .env_show import EnvShowCommand
from .health import HealthCommand
from .version import VersionCommand

__all__ = [
    "CallEvalCommand",
    "CallLogsCommand",
    "EnvInitCommand",
    "EnvShowCommand",
    "HealthCommand",
    "VersionCommand",
]
