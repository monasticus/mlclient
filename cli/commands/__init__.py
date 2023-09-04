"""The ML Client CLI Commands package.

It contains all CLI commands modules:
    * call_logs
        The Call Logs Command module.

It exports the following commands:
    * CallLogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
"""
from .call_logs import CallLogsCommand

__all__ = ["CallLogsCommand"]
