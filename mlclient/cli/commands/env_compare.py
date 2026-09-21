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
from mlclient.env import find_mlclient_directory
from mlclient.exceptions import MLClientDirectoryNotFoundError, WrongParametersError

_FILE_PREFIX = "mlclient-"
_FILE_SUFFIX = ".yaml"


class EnvCompareCommand(Command):
    """Compares settings across MLClient environments side by side.

    The twin of ``env show``: it resolves and masks the same way, but renders a
    table whose columns are environments and whose rows are settings. A value
    identical across every environment is green; a value that differs, or that is
    missing from some environment, is yellow. Secrets are masked unless
    ``--secrets`` is passed; comparison still uses the real values, so differing
    secrets show as differing even while masked. With no names every environment
    in the directory is compared. Each app server gets its own table, matched by
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
        configs = self._load(directory, names)
        self._announce_source(directory)
        self._render(names, configs)
        return 0

    def _load(
        self,
        directory: Path,
        names: list[str],
    ) -> dict[str, dict]:
        """Read each named environment, failing on the first one that is missing."""
        configs = {}
        for name in names:
            path = directory / f"{_FILE_PREFIX}{name}{_FILE_SUFFIX}"
            if not path.is_file():
                raise WrongParametersError(_unknown_env_message(name, directory))
            configs[name] = _read_config(path)
        return configs

    def _render(
        self,
        names: list[str],
        configs: dict[str, dict],
    ) -> None:
        """Render the root settings, then one table per app server matched by id."""
        reveal = self.option("secrets")
        roots = {name: _without_app_servers(configs[name]) for name in names}
        self._render_table(_title("Environments"), names, roots, reveal=reveal)
        for server_id, per_env in _servers_by_id(names, configs).items():
            self._render_table(_title(server_id), names, per_env, reveal=reveal)

    def _render_table(
        self,
        title: str,
        names: list[str],
        configs: dict[str, dict],
        *,
        reveal: bool,
    ) -> None:
        """Render one row per setting, one column per environment."""
        table = Table(self.io, style="box")
        table.set_header_title(title)
        table.set_headers([_header("Setting"), *(_header(name) for name in names)])
        for setting in _union_keys(names, configs):
            identical = _is_identical(setting, names, configs)
            cells = [
                _compare_cell(
                    setting, configs[name], reveal=reveal, identical=identical,
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


def _without_app_servers(
    config: dict,
) -> dict:
    """Return the root settings, leaving app servers to their own tables."""
    return {key: value for key, value in config.items() if key != _APP_SERVERS_KEY}


def _servers_by_id(
    names: list[str],
    configs: dict[str, dict],
) -> dict[str, dict[str, dict]]:
    """Group app servers by id, mapping each id to its per-environment settings.

    Ids keep first-seen order across the environments. Every id maps every
    environment name to that server's settings without its id, or an empty
    mapping when the environment has no such server, so a missing server renders
    as blank cells rather than dropping the column.
    """
    grouped: dict[str, dict[str, dict]] = {}
    for name in names:
        for server in configs[name].get(_APP_SERVERS_KEY) or []:
            per_env = grouped.setdefault(server["id"], {n: {} for n in names})
            per_env[name] = {k: v for k, v in server.items() if k != "id"}
    return grouped


def _union_keys(
    names: list[str],
    configs: dict[str, dict],
) -> list[str]:
    """Collect every setting across the environments, keeping first-seen order."""
    keys: list[str] = []
    for name in names:
        for key in configs[name]:
            if key not in keys:
                keys.append(key)
    return keys


def _is_identical(
    setting: str,
    names: list[str],
    configs: dict[str, dict],
) -> bool:
    """Tell whether every environment sets the setting to the same raw value."""
    if any(setting not in configs[name] for name in names):
        return False
    values = [configs[name][setting] for name in names]
    return all(value == values[0] for value in values)


def _compare_cell(
    setting: str,
    config: dict,
    *,
    reveal: bool,
    identical: bool,
) -> str:
    """Render one environment's value: dim when absent, green if shared, else yellow."""
    if setting not in config:
        return "<fg=blue>-</>"
    text = _display_value(setting, config[setting], reveal=reveal)
    color = "green" if identical else "yellow"
    return f"<fg={color}>{text}</>"
