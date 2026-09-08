"""The Env Show Command module.

It exports an implementation for 'env show' command:
    * EnvShowCommand
        Lists MLClient environments, or renders one environment's settings.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.ui.table import Table

from mlclient import constants, find_mlclient_directory
from mlclient.cli.commands.env_init import (
    ADMIN_PORT,
    APP_SERVICES_PORT,
    HEALTH_PORT,
    MANAGE_PORT,
)
from mlclient.exceptions import MLClientDirectoryNotFoundError, WrongParametersError

_FILE_PREFIX = "mlclient-"
_FILE_SUFFIX = ".yaml"
_SECRET_MASK = "****"
_APP_SERVERS_KEY = "app-servers"
_PREDEFINED_SERVERS = {
    "app-services": {"id": "app-services", "port": APP_SERVICES_PORT, "rest": True},
    "manage": {"id": "manage", "port": MANAGE_PORT},
    "admin": {"id": "admin", "port": ADMIN_PORT},
    "health": {"id": "health", "port": HEALTH_PORT, "auth": "app"},
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
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        name = self.argument("name")
        if name:
            return self._show(name)
        return self._list()

    def _list(
        self,
    ) -> int:
        """Print the environment names found in the .mlclient directory."""
        directory = self._env_dir()
        names = _env_names(directory)
        if not names:
            self.line(f"No environments found in <info>{directory}</info>")
            return 0
        self._announce_source(directory, directory)
        for name in names:
            self.line(name)
        return 0

    def _show(
        self,
        name: str,
    ) -> int:
        """Render one environment's settings, masking secrets."""
        directory = self._env_dir()
        path = directory / f"{_FILE_PREFIX}{name}{_FILE_SUFFIX}"
        if not path.is_file():
            raise WrongParametersError(_unknown_env_message(name, directory))
        if self.option("raw"):
            self.line(Formatter.escape(path.read_text().rstrip("\n")))
            return 0
        self._announce_source(directory, path)
        config = yaml.safe_load(path.read_text()) or {}
        servers = config.pop(_APP_SERVERS_KEY, None) or []
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
            return 0
        server = _find_server(setting, servers)
        if server is not None:
            self._render_settings(
                setting,
                {k: v for k, v in server.items() if k != "id"},
                reveal=reveal,
            )
            return 0
        message = f"No setting [{setting}]."
        raise WrongParametersError(message)

    def _render_settings(
        self,
        name: str,
        config: dict,
        *,
        reveal: bool,
    ) -> None:
        """Render the environment-level settings as a key/value table."""
        table = Table(self.io, style="box")
        table.set_header_title(_title(name))
        table.set_headers([_header("Setting"), _header("Value")])
        for key, value in config.items():
            table.add_row([_key(key), _styled_value(key, value, reveal=reveal)])
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
        table.set_header_title(_title("App Servers"))
        table.set_headers([_header(column) for column in columns])
        for server in servers:
            table.add_row(
                [
                    _styled_server_cell(column, server.get(column), reveal=reveal)
                    for column in columns
                ],
            )
        table.render()

    def _env_dir(
        self,
    ) -> Path:
        """Locate the .mlclient directory: home when --global, else nearest ancestor."""
        if self.option("global"):
            return Path.home() / constants.ML_CLIENT_DIR
        try:
            return find_mlclient_directory(Path.cwd())
        except MLClientDirectoryNotFoundError:
            return Path.cwd() / constants.ML_CLIENT_DIR

    def _announce_source(
        self,
        directory: Path,
        source: Path,
    ) -> None:
        """Name what is being read, flagging an implicit fall-through to global.

        Stays silent when the directory is the current one's default or was asked
        for explicitly with --global; only a surprising source is worth naming.
        """
        if self.option("global") or directory == Path.cwd() / constants.ML_CLIENT_DIR:
            return
        scope = (
            " (global)" if directory == Path.home() / constants.ML_CLIENT_DIR else ""
        )
        self.line(
            f"<options=italic>Reading <fg=green;options=italic>{source}</>{scope}</>\n",
        )


def _env_names(
    directory: Path,
) -> list[str]:
    """List environment names from the .mlclient directory's config files."""
    return sorted(
        path.name.removeprefix(_FILE_PREFIX).removesuffix(_FILE_SUFFIX)
        for path in directory.glob(f"{_FILE_PREFIX}*{_FILE_SUFFIX}")
    )


def _unknown_env_message(
    name: str,
    directory: Path,
) -> str:
    """Report the unknown environment, listing the ones that do exist."""
    names = _env_names(directory)
    available = f" Available: {', '.join(names)}." if names else ""
    return f"No environment [{name}] in {directory}.{available}"


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
    columns: list[str] = []
    for server in servers:
        for key in server:
            if key not in columns:
                columns.append(key)
    return columns


def _title(text: str) -> str:
    return f"<fg=magenta;options=bold>{text}</>"


def _header(text: str) -> str:
    return f"<fg=cyan;options=bold>{text}</>"


def _key(text: str) -> str:
    return f"<fg=cyan>{text}</>"


def _styled_server_cell(
    column: str,
    value: object,
    *,
    reveal: bool,
) -> str:
    """Colour an app server's name; other columns follow value semantics."""
    if column == "id":
        return _key(str(value))
    return _styled_value(column, value, reveal=reveal)


def _styled_value(
    key: str,
    value: object,
    *,
    reveal: bool = False,
) -> str:
    """Colour a setting value by its meaning, masking secrets."""
    text = _display_value(key, value, reveal=reveal)
    if _is_secret(key) and value is not None:
        return f"<fg=red>{text}</>"
    if value is None:
        return f"<fg=blue>{text}</>"
    if isinstance(value, bool):
        return f"<fg=green>{text}</>" if value else f"<fg=yellow>{text}</>"
    return text


def _display_value(
    key: str,
    value: object,
    *,
    reveal: bool = False,
) -> str:
    """Render a setting value for the table, masking secrets."""
    if value is None:
        return "-"
    if _is_secret(key) and not reveal:
        return _SECRET_MASK
    if isinstance(value, dict):
        return ", ".join(
            f"{k}={_display_value(k, v, reveal=reveal)}" for k, v in value.items()
        )
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _is_secret(
    key: str,
) -> bool:
    """Tell whether a key holds a secret that must be masked."""
    normalized = key.lower().replace("-", "_")
    return "password" in normalized or normalized == "api_key"
