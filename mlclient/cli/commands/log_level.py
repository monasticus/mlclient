"""The Log Level Command module.

It exports an implementation for 'log-level' command:
    * LogLevelCommand
        Shows or sets a MarkLogic file/system log level.
"""

from __future__ import annotations

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.formatters.formatter import Formatter
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient import MLClientManager
from mlclient.exceptions import MarkLogicError, WrongParametersError
from mlclient.services import LogLevelService

# Cool-to-warm severity ramp; within each hue pair the more severe level takes
# the light variant. The fine/debug/info/warning/error/critical colours match
# the logger palette in CleoAppHandler.setup_for.
_LEVEL_COLORS = {
    "finest": "blue",
    "finer": "light_blue",
    "fine": "cyan",
    "debug": "light_cyan",
    "config": "green",
    "info": "light_green",
    "notice": "yellow",
    "warning": "light_yellow",
    "error": "red",
    "critical": "light_red",
    "alert": "magenta",
    "emergency": "light_magenta",
}


class LogLevelCommand(Command):
    """Shows or sets a MarkLogic file/system log level.

    With a level argument it sets the level; without one it shows the current
    level. Evaluates the Admin functions on the connected REST App-Server and,
    only when that user lacks the privileges, falls back to the Management REST
    API.

    The REST App-Server the command connects to (``-s``) is distinct from the
    App Server whose log level is shown or set (``--server``).

    Usage:
      log-level [options] [<level>]

    Arguments:
      level
            The log level to set. Omit to show the current level.

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
      -s, --rest-server=REST-SERVER
            The ML REST Server environmental id
          --type=TYPE
            The log type: file or system [default: "file"]
          --group=GROUP
            The group to target [default: "Default"]
          --server=SERVER
            The App Server to target (file log level only)
    """

    name: str = "log-level"
    description: str = "Shows or sets a MarkLogic file/system log level"
    arguments: list[Argument] = [
        argument(
            "level",
            description="The log level to set. Omit to show the current level.",
            optional=True,
        ),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
        ),
        option(
            "rest-server",
            "s",
            description="The ML REST Server environmental id",
            flag=False,
        ),
        option(
            "type",
            description="The log type: file or system",
            flag=False,
            default="file",
        ),
        option(
            "group",
            description="The group to target",
            flag=False,
            default="Default",
        ),
        option(
            "server",
            description="The App Server to target (file log level only)",
            flag=False,
        ),
    ]

    def handle(self) -> int:
        """Execute the command."""
        level = self.argument("level")
        log_type = self.option("type")
        group = self.option("group")
        server = self.option("server")

        manager = MLClientManager(self.option("environment"))
        with manager.get_client(self.option("rest-server")) as ml:
            service = LogLevelService(ml.rest, ml.manage)
            try:
                if level is None:
                    current = service.get(group=group, server=server, log_type=log_type)
                else:
                    current = service.set(
                        level, group=group, server=server, log_type=log_type,
                    )
            except (MarkLogicError, WrongParametersError) as exc:
                self.line_error(Formatter.escape(str(exc)))
                return 1

        self._print_result(group, server, log_type, current)
        return 0

    def _print_result(
        self,
        group: str,
        server: str | None,
        log_type: str,
        level: str,
    ) -> None:
        """Print the target names and styled log level.

        Parameters
        ----------
        group : str
            Group name displayed literally
        server : str | None
            Optional App Server name displayed literally
        log_type : str
            File or system log selector
        level : str
            Level returned by the service
        """
        self.line(f"Group: <options=bold>{Formatter.escape(group)}</>")
        if server is not None:
            self.line(f"App Server: <options=bold>{Formatter.escape(server)}</>")
        label = "System Log Level" if log_type == "system" else "File Log Level"
        self.line(f"{label}: {self._styled_level(level)}")

    @staticmethod
    def _styled_level(level: str) -> str:
        """Format a known level in colour, or an unknown level in bold.

        Parameters
        ----------
        level : str
            Level to display literally

        Returns
        -------
        str
            Escaped level surrounded by Cleo formatting tags
        """
        color = _LEVEL_COLORS.get(level)
        if color is None:
            return f"<options=bold>{Formatter.escape(level)}</>"
        return f"<fg={color};options=bold>{Formatter.escape(level)}</>"
