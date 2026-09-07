"""The ML Client CLI Commands package.

It contains all CLI commands modules:
    * call_eval
        The Call Eval Command module.
    * call_logs
        The Call Logs Command module.
    * env_init
        The Env Init Command module.

It exports the following commands:
    * CallEvalCommand
        Sends a GET request to the /v1/eval endpoint.
    * CallLogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
    * EnvInitCommand
        Scaffolds an MLClient environment configuration file.
"""

from .call_eval import CallEvalCommand
from .call_logs import CallLogsCommand
from .env_init import EnvInitCommand

__all__ = ["CallEvalCommand", "CallLogsCommand", "EnvInitCommand"]
