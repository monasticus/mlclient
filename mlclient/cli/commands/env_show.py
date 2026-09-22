"""The Env Show Command module.

It exports an implementation for 'env show' command:
    * EnvShowCommand
        Lists MLClient environments, or renders one environment's settings.
"""

from __future__ import annotations

import os
import subprocess
import sys

from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.ui.table import Table

from mlclient.cli.commands._env_common import (
    APP_SERVERS_KEY,
    FILE_PREFIX,
    FILE_SUFFIX,
    announce_source,
    display_value,
    effective_config,
    env_names,
    header,
    is_secret,
    key,
    read_config,
    resolve_env_dir,
    title,
    unknown_env_message,
)
from mlclient.connection import MARKLOGIC_APP_SERVICES_PORT
from mlclient.env import DEFAULT_APP_SERVER_SETTINGS
from mlclient.exceptions import WrongParametersError

_PREDEFINED_SERVERS = {
    server["id"]: {
        "id": server["id"],
        "port": MARKLOGIC_APP_SERVICES_PORT,
        **server,
    }
    for server in DEFAULT_APP_SERVER_SETTINGS
}


class EnvShowCommand(Command):
    """Command reading .mlclient environment files.

    With no name it lists the environments found in the .mlclient directory;
    with a name it renders that environment's settings as a table, with the app
    servers in a second table, masking secrets. A second argument narrows the
    view to a single root setting (its value is printed) or a single app server
    (rendered as a key/value table). ``--global`` reads the home directory
    instead of the current one.

    Usage:
      env show [options] [--] [<name>] [<setting>]

    Arguments:
      name
            The environment name. Omit to list the available environments.
      setting
            A root setting name (host, protocol, ...) or an app server id.

    Options:
      -g, --global
            Read from the home directory instead of the current directory
          --raw
            Print the raw configuration file instead of a rendered table
      -s, --secrets
            Reveal secret values instead of masking them
      -d, --defaults
            Fill in inherited defaults and the always-present app servers
      -c, --copy
            Copy a simple setting value to the clipboard, including secrets
    """

    name: str = "env show"
    description: str = (
        "Lists MLClient environments, or renders one environment's settings"
    )
    arguments: list[Argument] = [
        argument(
            "name",
            "The environment name. Omit to list the available environments.",
            optional=True,
        ),
        argument(
            "setting",
            "A root setting name (host, protocol, ...) or an app server id.",
            optional=True,
        ),
    ]
    options: list[Option] = [
        option(
            "global",
            "g",
            description="Read from the home directory instead of the current directory",
        ),
        option(
            "raw",
            description="Print the raw configuration file instead of a rendered table",
        ),
        option(
            "secrets",
            "s",
            description="Reveal secret values instead of masking them",
        ),
        option(
            "defaults",
            "d",
            description=(
                "Fill in inherited defaults and the always-present app servers"
            ),
        ),
        option(
            "copy",
            "c",
            description=(
                "Copy a simple setting value to the clipboard, including secrets"
            ),
        ),
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        name = self.argument("name")
        status = self._show(name) if name else self._list()
        if self.option("copy") and (not self.argument("setting") or self.option("raw")):
            self.line_error(
                "--copy only works for individual settings without --raw; "
                "ignoring --copy.",
                style="fg=yellow;options=dark",
            )
        return status

    def _list(
        self,
    ) -> int:
        """Print the environment names found in the .mlclient directory."""
        directory = resolve_env_dir(self)
        names = env_names(directory)
        if not names:
            directory_name = Formatter.escape(str(directory))
            self.line(f"No environments found in <info>{directory_name}</info>")
            return 0
        announce_source(self, directory, directory)
        for name in names:
            self.line(Formatter.escape(name))
        return 0

    def _show(
        self,
        name: str,
    ) -> int:
        """Render one environment's settings, masking secrets."""
        directory = resolve_env_dir(self)
        path = directory / f"{FILE_PREFIX}{name}{FILE_SUFFIX}"
        if not path.is_file():
            raise WrongParametersError(unknown_env_message(name, directory))
        if self.option("raw"):
            self.line(Formatter.escape(path.read_text().rstrip("\n")))
            return 0
        announce_source(self, directory, path)
        config = read_config(path)
        if self.option("defaults"):
            config, servers = effective_config(path, config)
        else:
            servers = config.pop(APP_SERVERS_KEY, None) or []
        reveal = self.option("secrets")
        setting = self.argument("setting")
        if setting:
            return self._show_setting(setting, config, servers, reveal=reveal)
        self._render_settings(name, config, reveal=reveal)
        if servers:
            self._render_servers(servers, reveal=reveal)
        return 0

    def _show_setting(
        self,
        setting: str,
        config: dict,
        servers: list[dict],
        *,
        reveal: bool,
    ) -> int:
        """Print a single root setting, or render one app server as a table."""
        if setting in config:
            self.line(_styled_value(setting, config[setting], reveal=reveal))
            self._copy_setting(setting, config[setting])
            return 0
        server = _find_server(setting, servers)
        if server is not None:
            self._render_settings(
                setting,
                {k: v for k, v in server.items() if k != "id"},
                reveal=reveal,
            )
            self._copy_setting(setting, server)
            return 0
        message = Formatter.escape(f"No setting [{setting}].")
        raise WrongParametersError(message)

    def _copy_setting(self, setting: str, value: object) -> None:
        """Copy an unmasked scalar while keeping clipboard failures non-fatal."""
        if not self.option("copy"):
            return
        if not isinstance(value, (str, int, float, bool)):
            self.line_error(
                "--copy only works for simple values "
                "(text, numbers, booleans); ignoring --copy.",
                style="fg=yellow;options=dark",
            )
            return
        try:
            _copy_to_clipboard(display_value(setting, value, reveal=True))
        except (OSError, subprocess.SubprocessError):
            self.line_error(
                "Could not copy to clipboard. Check that a clipboard "
                "tool and a desktop session are available.",
                style="fg=yellow;options=dark",
            )
            return
        self.line("Copied to clipboard.", style="fg=green;options=italic")

    def _render_settings(
        self,
        name: str,
        config: dict,
        *,
        reveal: bool,
    ) -> None:
        """Render the environment-level settings as a key/value table."""
        table = Table(self.io, style="box")
        table.set_header_title(title(name))
        table.set_headers([header("Setting"), header("Value")])
        for field, value in config.items():
            table.add_row([key(field), _styled_value(field, value, reveal=reveal)])
        table.render()

    def _render_servers(
        self,
        servers: list[dict],
        *,
        reveal: bool,
    ) -> None:
        """Render the app servers as a table, one row per server."""
        columns = _server_columns(servers)
        table = Table(self.io, style="box")
        table.set_header_title(title("App Servers"))
        table.set_headers([header(column) for column in columns])
        for server in servers:
            table.add_row(
                [
                    _styled_server_cell(column, server.get(column), reveal=reveal)
                    for column in columns
                ],
            )
        table.render()


def _copy_to_clipboard(text: str) -> None:
    """Send text through stdin to the platform's clipboard tool."""
    encoding = "utf-8"
    if sys.platform == "win32":
        command = ["clip"]
        encoding = "utf-16"
    elif sys.platform == "darwin":
        command = ["pbcopy"]
    elif os.environ.get("WAYLAND_DISPLAY"):
        command = ["wl-copy"]
    else:
        command = ["xclip", "-selection", "clipboard"]
    subprocess.run(
        command,
        input=text.encode(encoding),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )


def _find_server(
    setting: str,
    servers: list[dict],
) -> dict | None:
    """Return a server from the file, falling back to a predefined default."""
    configured = next((s for s in servers if s.get("id") == setting), None)
    if configured is not None:
        return configured
    return _PREDEFINED_SERVERS.get(setting)


def _server_columns(
    servers: list[dict],
) -> list[str]:
    """Collect the union of server keys, keeping first-seen order."""
    return list(dict.fromkeys(field for server in servers for field in server))


def _styled_server_cell(
    column: str,
    value: object,
    *,
    reveal: bool,
) -> str:
    """Colour an app server's name; other columns follow value semantics."""
    if column == "id":
        return key(str(value))
    return _styled_value(column, value, reveal=reveal)


def _styled_value(
    setting: str,
    value: object,
    *,
    reveal: bool = False,
) -> str:
    """Colour a setting value by its meaning, masking secrets."""
    text = Formatter.escape(display_value(setting, value, reveal=reveal))
    if is_secret(setting) and value is not None:
        return f"<fg=red>{text}</>"
    if value is None:
        return f"<fg=blue>{text}</>"
    if isinstance(value, bool):
        return f"<fg=green>{text}</>" if value else f"<fg=yellow>{text}</>"
    return text
