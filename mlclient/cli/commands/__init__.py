"""The ML Client CLI Commands package.

It contains all CLI commands modules:
    * call_eval
        The Call Eval Command module.
    * call_logs
        The Call Logs Command module.
    * init_env
        The Init Env Command module.

It exports the following commands:
    * CallEvalCommand
        Sends a GET request to the /v1/eval endpoint.
    * CallLogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
    * InitEnvCommand
        Scaffolds an MLClient environment configuration file.
"""

from .call_eval import CallEvalCommand
from .call_logs import CallLogsCommand
from .init_env import InitEnvCommand

__all__ = ["CallEvalCommand", "CallLogsCommand", "InitEnvCommand"]
