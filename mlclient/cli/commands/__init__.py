"""The ML Client CLI Commands package.

It contains all CLI commands modules:
    * call_eval
        The Call Eval Command module.
    * call_logs
        The Call Logs Command module.

It exports the following commands:
    * CallEvalCommand
        Sends a GET request to the /v1/eval endpoint.
    * CallLogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
"""
from .call_eval import CallEvalCommand
from .call_logs import CallLogsCommand

__all__ = ["CallEvalCommand", "CallLogsCommand"]
