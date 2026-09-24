"""The Env Compare Command module.

It exports an implementation for 'env compare' command:
    * EnvCompareCommand
        Compares settings across MLClient environments side by side.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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
    key,
    read_config,
    resolve_env_dir,
    title,
    unknown_env_message,
)
from mlclient.exceptions import WrongParametersError

if TYPE_CHECKING:
    from pathlib import Path


class EnvCompareCommand(Command):
    """Compares settings across MLClient environments side by side.

    The twin of ``env show``: it resolves and masks the same way, but renders a
    table whose columns are environments and whose rows are settings. A value
    shared by every environment is green even where a default supplies it; a
    default that differs from what another environment set is blue; an explicit
    value that differs is yellow. A value an environment left to its default is
    tagged with an italic ``(default)``. A setting left to its default
    everywhere is dropped when equal unless ``--defaults`` asks for it. Secrets
    are masked unless ``--secrets`` is passed; comparison uses the real values, so
    differing secrets show as differing even while masked. With no names every
    environment in the directory is compared; ``--exclude`` drops named
    environments from that set. Each app server gets its own table, matched by
    id across environments.

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
      -d, --defaults
            Keep settings left to their default in every environment
      -e, --exclude
            Environment to leave out of the comparison
    """

    name: str = "env compare"
    description: str = "Compares settings across MLClient environments side by side"
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
        option(
            "defaults",
            "d",
            description="Keep settings left to their default in every environment",
        ),
        option(
            "exclude",
            "e",
            description="Environment to leave out of the comparison",
            flag=False,
            multiple=True,
        ),
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        directory = resolve_env_dir(self)
        names = self.argument("names") or env_names(directory)
        excluded = set(self.option("exclude"))
        names = [name for name in names if name not in excluded]
        if not names:
            directory_name = Formatter.escape(str(directory))
            self.line(f"No environments found in <info>{directory_name}</info>")
            return 0
        views = self._load(directory, names)
        announce_source(self, directory, directory)
        self._render(names, views, show_defaults=self.option("defaults"))
        return 0

    def _load(
        self,
        directory: Path,
        names: list[str],
    ) -> dict[str, _EnvView]:
        """Resolve each named environment, failing on the first one missing."""
        views = {}
        for name in names:
            path = directory / f"{FILE_PREFIX}{name}{FILE_SUFFIX}"
            if not path.is_file():
                raise WrongParametersError(unknown_env_message(name, directory))
            views[name] = _env_view(path)
        return views

    def _render(
        self,
        names: list[str],
        views: dict[str, _EnvView],
        *,
        show_defaults: bool,
    ) -> None:
        """Render the root settings, then one table per app server matched by id."""
        reveal = self.option("secrets")
        roots = {name: views[name].root for name in names}
        root_explicit = {name: views[name].root_explicit for name in names}
        self._render_table(
            title("Environments"),
            roots,
            root_explicit,
            reveal=reveal,
            show_defaults=show_defaults,
        )
        for server_id in _server_ids(names, views):
            values = {name: views[name].server_values(server_id) for name in names}
            explicit = {name: views[name].server_explicit(server_id) for name in names}
            self._render_table(
                title(server_id),
                values,
                explicit,
                reveal=reveal,
                show_defaults=show_defaults,
            )

    def _render_table(
        self,
        table_title: str,
        values: dict[str, dict],
        explicit: dict[str, set[str]],
        *,
        reveal: bool,
        show_defaults: bool,
    ) -> None:
        """Render one row per setting, one column per environment.

        Equal settings left to defaults in every environment are dropped unless
        kept by ``show_defaults``. Differing inherited values and missing servers
        remain visible. A table with no rows left is not rendered.
        """
        names = list(values)
        settings = _visible_settings(
            names,
            values,
            explicit,
            show_defaults=show_defaults,
        )
        if not settings:
            return
        table = Table(self.io, style="box")
        table.set_header_title(table_title)
        table.set_headers([header("Setting"), *(header(name) for name in names)])
        for setting in settings:
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
            table.add_row([key(setting), *cells])
        table.render()


@dataclass
class _EnvView:
    """An environment's effective settings and which ones the user set explicitly.

    Values come from a resolved MLEnvironment, so defaults (the admin
    credentials, the always-present app servers) are filled in; the explicit
    sets come from the raw YAML, so a filled-in default can be told apart from a
    value the user actually wrote.
    """

    root: dict
    root_explicit: set[str]
    servers: dict[str, _ServerView]

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


@dataclass
class _ServerView:
    """One app server's effective settings and the settings the user set."""

    values: dict
    explicit: set[str]


def _env_view(
    path: Path,
) -> _EnvView:
    """Resolve an environment to effective values, tracking which the user set."""
    raw = read_config(path)
    root, resolved_servers = effective_config(path, raw)
    root_explicit = {field for field in raw if field != APP_SERVERS_KEY}
    declared = _declared_servers(raw)
    servers = {}
    for server in resolved_servers:
        server_id = server["id"]
        values = {field: value for field, value in server.items() if field != "id"}
        servers[server_id] = _ServerView(values, set(declared.get(server_id, {})))
    return _EnvView(root, root_explicit, servers)


def _declared_servers(
    raw: dict,
) -> dict[str, dict]:
    """Map each app server id the user wrote to the raw fields given to it."""
    declared = {}
    for server in raw.get(APP_SERVERS_KEY) or []:
        declared[server["id"]] = {k: v for k, v in server.items() if k != "id"}
    return declared


def _server_ids(
    names: list[str],
    views: dict[str, _EnvView],
) -> list[str]:
    """Collect every app server id across the environments, keeping first-seen order."""
    return list(
        dict.fromkeys(server_id for name in names for server_id in views[name].servers),
    )


def _visible_settings(
    names: list[str],
    values: dict[str, dict],
    explicit: dict[str, set[str]],
    *,
    show_defaults: bool,
) -> list[str]:
    """Keep explicit or differing settings, and all defaults when requested."""
    settings = _union_keys(names, values)
    if show_defaults:
        return settings
    return [
        setting
        for setting in settings
        if any(setting in explicit[name] for name in names)
        or not _is_identical(setting, names, values)
    ]


def _union_keys(
    names: list[str],
    values: dict[str, dict],
) -> list[str]:
    """Collect every setting across the environments, keeping first-seen order."""
    return list(dict.fromkeys(field for name in names for field in values[name]))


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
    """Render one environment's value, coloured to place it in the comparison.

    A value shared by every environment is green even where a default supplies
    it; a default that differs from what another environment set is blue; an
    explicit value that differs is yellow; an absent setting is a dim dash. A
    value an environment left to its default is tagged with an italic
    ``(default)``.
    """
    if setting not in values:
        return "<fg=default;options=dark>-</>"
    text = Formatter.escape(display_value(setting, values[setting], reveal=reveal))
    if identical:
        color = "green"
    elif default:
        color = "blue"
    else:
        color = "yellow"
    cell = f"<fg={color}>{text}</>"
    if default:
        cell += " <options=italic>(default)</>"
    return cell
