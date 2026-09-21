"""The Env Compare Command module.

It exports an implementation for 'env compare' command:
    * EnvCompareCommand
        Compares settings across MLClient environments side by side.
"""

from __future__ import annotations

from pathlib import Path

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.ui.table import Table

from mlclient import _constants as constants
from mlclient.cli.commands.env_show import (
    _APP_SERVERS_KEY,
    _display_value,
    _env_names,
    _header,
    _key,
    _read_config,
    _title,
    _unknown_env_message,
)
from mlclient.env import MLEnvironment, find_mlclient_directory
from mlclient.exceptions import MLClientDirectoryNotFoundError, WrongParametersError

_FILE_PREFIX = "mlclient-"
_FILE_SUFFIX = ".yaml"


class EnvCompareCommand(Command):
    """Compares settings across MLClient environments side by side.

    The twin of ``env show``: it resolves and masks the same way, but renders a
    table whose columns are environments and whose rows are settings. Each cell
    holds the environment's effective value, so a setting an environment leaves
    to its default (the ``admin`` credentials, the platform app servers) still
    appears, shown blue to flag that the environment did not set it. An
    explicit value identical across every environment is green; one that
    differs is yellow. Secrets are masked unless ``--secrets`` is passed;
    comparison still uses the real values, so differing secrets show as
    differing even while masked. With no names every environment in the
    directory is compared. Each app server gets its own table, matched by id
    across environments.

    Usage:
      env compare [options] [--] [<names>...]

    Arguments:
      names
            The environment names to compare. Omit to compare them all.

    Options:
      -g, --global
            Read from the home directory instead of the current directory
      -s, --secrets
            Reveal secret values instead of masking them
    """

    name: str = "env compare"
    description: str = (
        "Compares settings across MLClient environments side by side"
    )
    arguments: list[Argument] = [
        argument(
            "names",
            "The environment names to compare. Omit to compare them all.",
            optional=True,
            multiple=True,
        ),
    ]
    options: list[Option] = [
        option(
            "global",
            "g",
            description="Read from the home directory instead of the current directory",
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
        directory = self._env_dir()
        names = self.argument("names") or _env_names(directory)
        if not names:
            self.line(f"No environments found in <info>{directory}</info>")
            return 0
        views = self._load(directory, names)
        self._announce_source(directory)
        self._render(names, views)
        return 0

    def _load(
        self,
        directory: Path,
        names: list[str],
    ) -> dict[str, _EnvView]:
        """Resolve each named environment, failing on the first one missing."""
        views = {}
        for name in names:
            path = directory / f"{_FILE_PREFIX}{name}{_FILE_SUFFIX}"
            if not path.is_file():
                raise WrongParametersError(_unknown_env_message(name, directory))
            views[name] = _env_view(path)
        return views

    def _render(
        self,
        names: list[str],
        views: dict[str, _EnvView],
    ) -> None:
        """Render the root settings, then one table per app server matched by id."""
        reveal = self.option("secrets")
        roots = {name: views[name].root for name in names}
        root_explicit = {name: views[name].root_explicit for name in names}
        self._render_table(
            _title("Environments"), names, roots, root_explicit, reveal=reveal,
        )
        for server_id in _server_ids(names, views):
            values = {name: views[name].server_values(server_id) for name in names}
            explicit = {name: views[name].server_explicit(server_id) for name in names}
            self._render_table(
                _title(server_id), names, values, explicit, reveal=reveal,
            )

    def _render_table(
        self,
        title: str,
        names: list[str],
        values: dict[str, dict],
        explicit: dict[str, set[str]],
        *,
        reveal: bool,
    ) -> None:
        """Render one row per setting, one column per environment."""
        table = Table(self.io, style="box")
        table.set_header_title(title)
        table.set_headers([_header("Setting"), *(_header(name) for name in names)])
        for setting in _union_keys(names, values):
            identical = _is_identical(setting, names, values)
            cells = [
                _compare_cell(
                    setting,
                    values[name],
                    default=setting not in explicit[name],
                    reveal=reveal,
                    identical=identical,
                )
                for name in names
            ]
            table.add_row([_key(setting), *cells])
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
    ) -> None:
        """Name the directory read, flagging an implicit fall-through to global."""
        source = directory
        if self.option("global") or source == Path.cwd() / constants.ML_CLIENT_DIR:
            return
        scope = " (global)" if source == Path.home() / constants.ML_CLIENT_DIR else ""
        self.line(
            f"<options=italic>Reading <fg=green;options=italic>{source}</>{scope}</>\n",
        )


class _EnvView:
    """An environment's effective settings and which ones the user set explicitly.

    Values come from a resolved MLEnvironment, so defaults (the admin
    credentials, the always-present app servers) are filled in; the explicit
    sets come from the raw YAML, so a filled-in default can be told apart from a
    value the user actually wrote.
    """

    def __init__(
        self,
        root: dict,
        root_explicit: set[str],
        servers: dict[str, _ServerView],
    ) -> None:
        self.root = root
        self.root_explicit = root_explicit
        self.servers = servers

    def server_values(
        self,
        server_id: str,
    ) -> dict:
        """Return the effective settings of the named server, or an empty mapping."""
        server = self.servers.get(server_id)
        return server.values if server else {}

    def server_explicit(
        self,
        server_id: str,
    ) -> set[str]:
        """Return the settings the user set on the named server, or an empty set."""
        server = self.servers.get(server_id)
        return server.explicit if server else set()


class _ServerView:
    """One app server's effective settings and the settings the user set."""

    def __init__(
        self,
        values: dict,
        explicit: set[str],
    ) -> None:
        self.values = values
        self.explicit = explicit


def _env_view(
    path: Path,
) -> _EnvView:
    """Resolve an environment to effective values, tracking which the user set."""
    raw = _read_config(path)
    environment = MLEnvironment.load_file(str(path))
    root = environment.model_dump(
        mode="json", by_alias=True, exclude_none=True, exclude={"app_servers"},
    )
    root_explicit = {key for key in raw if key != _APP_SERVERS_KEY}
    declared = _declared_servers(raw)
    servers = {}
    for server in environment.app_servers:
        values = server.model_dump(
            mode="json", by_alias=True, exclude_none=True, exclude={"identifier"},
        )
        servers[server.identifier] = _ServerView(
            values, set(declared.get(server.identifier, {})),
        )
    return _EnvView(root, root_explicit, servers)


def _declared_servers(
    raw: dict,
) -> dict[str, dict]:
    """Map each app server id the user wrote to the raw fields given to it."""
    declared = {}
    for server in raw.get(_APP_SERVERS_KEY) or []:
        declared[server["id"]] = {k: v for k, v in server.items() if k != "id"}
    return declared


def _server_ids(
    names: list[str],
    views: dict[str, _EnvView],
) -> list[str]:
    """Collect every app server id across the environments, keeping first-seen order."""
    ids: list[str] = []
    for name in names:
        for server_id in views[name].servers:
            if server_id not in ids:
                ids.append(server_id)
    return ids


def _union_keys(
    names: list[str],
    values: dict[str, dict],
) -> list[str]:
    """Collect every setting across the environments, keeping first-seen order."""
    keys: list[str] = []
    for name in names:
        for key in values[name]:
            if key not in keys:
                keys.append(key)
    return keys


def _is_identical(
    setting: str,
    names: list[str],
    values: dict[str, dict],
) -> bool:
    """Tell whether every environment sets the setting to the same value."""
    if any(setting not in values[name] for name in names):
        return False
    resolved = [values[name][setting] for name in names]
    return all(value == resolved[0] for value in resolved)


def _compare_cell(
    setting: str,
    values: dict,
    *,
    default: bool,
    reveal: bool,
    identical: bool,
) -> str:
    """Render one environment's value: dim when absent, blue when left to a default.

    An explicit value shared by every environment is green; an explicit value
    that differs is yellow.
    """
    if setting not in values:
        return "<fg=default;options=dark>-</>"
    text = _display_value(setting, values[setting], reveal=reveal)
    if default:
        color = "blue"
    elif identical:
        color = "green"
    else:
        color = "yellow"
    return f"<fg={color}>{text}</>"
