"""Shared building blocks for the ``env`` commands.

Locating the ``.mlclient`` directory, reading and resolving a configuration,
masking secrets and styling table cells are the same across ``env show`` and
``env compare``. They live here so neither command reaches into the other.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from mlclient import _constants as constants
from mlclient.env import MLEnvironment, find_mlclient_directory
from mlclient.exceptions import MLClientDirectoryNotFoundError, WrongParametersError

if TYPE_CHECKING:
    from cleo.commands.command import Command

FILE_PREFIX = "mlclient-"
FILE_SUFFIX = ".yaml"
SECRET_MASK = "****"
APP_SERVERS_KEY = "app-servers"


def resolve_env_dir(
    command: Command,
) -> Path:
    """Locate the .mlclient directory: home when --global, else nearest ancestor."""
    if command.option("global"):
        return Path.home() / constants.ML_CLIENT_DIR
    try:
        return find_mlclient_directory(Path.cwd())
    except MLClientDirectoryNotFoundError:
        return Path.cwd() / constants.ML_CLIENT_DIR


def announce_source(
    command: Command,
    directory: Path,
    source: Path,
) -> None:
    """Name what is being read, flagging an implicit fall-through to global.

    Stays silent when the directory is the current one's default or was asked
    for explicitly with --global; only a surprising source is worth naming.
    """
    if command.option("global") or directory == Path.cwd() / constants.ML_CLIENT_DIR:
        return
    scope = " (global)" if directory == Path.home() / constants.ML_CLIENT_DIR else ""
    command.line(
        f"<options=italic>Reading <fg=green;options=italic>{source}</>{scope}</>\n",
    )


def env_names(
    directory: Path,
) -> list[str]:
    """List environment names from the .mlclient directory's config files."""
    return sorted(
        path.name.removeprefix(FILE_PREFIX).removesuffix(FILE_SUFFIX)
        for path in directory.glob(f"{FILE_PREFIX}*{FILE_SUFFIX}")
    )


def unknown_env_message(
    name: str,
    directory: Path,
) -> str:
    """Report the unknown environment, listing the ones that do exist."""
    names = env_names(directory)
    available = f" Available: {', '.join(names)}." if names else ""
    return f"No environment [{name}] in {directory}.{available}"


def read_config(
    path: Path,
) -> dict:
    """Read YAML and validate the structure needed to render an environment."""
    try:
        config = yaml.safe_load(path.read_text())
    except yaml.YAMLError:
        message = f"Invalid YAML in {path}."
        raise WrongParametersError(message) from None
    if config is None:
        return {}
    if not isinstance(config, dict):
        message = f"Environment in {path} must be a mapping."
        raise WrongParametersError(message)
    servers = config.get(APP_SERVERS_KEY)
    if servers is None:
        return config
    if not isinstance(servers, list):
        message = f"In {path}, app-servers must be a list."
        raise WrongParametersError(message)
    for server in servers:
        if (
            not isinstance(server, dict)
            or not isinstance(server.get("id"), str)
            or not server["id"].strip()
        ):
            message = (
                f"In {path}, each app server must be a mapping "
                "with a non-empty string id."
            )
            raise WrongParametersError(message)
    return config


def effective_config(
    path: Path,
) -> tuple[dict, list[dict]]:
    """Resolve an environment: root settings and app servers, defaults filled in.

    Values come from a resolved MLEnvironment, so the inherited connection
    defaults and the always-present App Services, Manage, Admin and Health
    servers appear even when the file does not spell them out.
    """
    environment = MLEnvironment.load_file(str(path))
    root = environment.model_dump(
        mode="json", by_alias=True, exclude_none=True, exclude={"app_servers"},
    )
    servers = [
        server.model_dump(mode="json", by_alias=True, exclude_none=True)
        for server in environment.app_servers
    ]
    return root, servers


def display_value(
    key: str,
    value: object,
    *,
    reveal: bool = False,
) -> str:
    """Render a setting value for a table cell, masking secrets."""
    if value is None:
        return "-"
    if is_secret(key) and not reveal:
        return SECRET_MASK
    if isinstance(value, dict):
        return ", ".join(
            f"{k}={display_value(k, v, reveal=reveal)}" for k, v in value.items()
        )
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(display_value(key, item, reveal=reveal) for item in value)
    return str(value)


def is_secret(
    key: str,
) -> bool:
    """Tell whether a key holds a secret that must be masked."""
    normalized = key.lower().replace("-", "_")
    return "password" in normalized or normalized == "api_key"


def title(text: str) -> str:
    """Style a table title."""
    return f"<fg=magenta;options=bold>{text}</>"


def header(text: str) -> str:
    """Style a table header cell."""
    return f"<fg=cyan;options=bold>{text}</>"


def key(text: str) -> str:
    """Style a setting name cell."""
    return f"<fg=cyan>{text}</>"
