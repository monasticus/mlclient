"""Shared building blocks for the ``env`` commands.

Locating the ``.mlclient`` directory, reading and resolving a configuration,
masking secrets and styling table cells are the same across ``env show`` and
``env compare``. They live here so neither command reaches into the other.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from cleo.formatters.formatter import Formatter
from pydantic import BaseModel, ValidationError

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
    source_name = Formatter.escape(str(source))
    command.line(
        "<options=italic>Reading "
        f"<fg=green;options=italic>{source_name}</>{scope}</>\n",
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
    return Formatter.escape(f"No environment [{name}] in {directory}.{available}")


def read_config(
    path: Path,
) -> dict:
    """Read YAML and validate the structure needed to render an environment."""
    config = _read_yaml(path)
    if config is None:
        return {}
    if not isinstance(config, dict):
        message = Formatter.escape(f"Environment in {path} must be a mapping.")
        raise WrongParametersError(message)
    servers = config.get(APP_SERVERS_KEY)
    if servers is None:
        return config
    if not isinstance(servers, list):
        message = Formatter.escape(f"In {path}, app-servers must be a list.")
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
            raise WrongParametersError(Formatter.escape(message))
    return config


def _read_yaml(path: Path) -> object:
    """Load YAML without retaining parser exceptions containing file contents."""
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError:
        message = Formatter.escape(f"Invalid YAML in {path}.")
    # Cleo also renders suppressed exception contexts at debug verbosity.
    raise WrongParametersError(message)


def _validate_environment(path: Path, raw: dict) -> MLEnvironment:
    """Validate settings, reporting field locations without secret input values."""
    data = {**raw, APP_SERVERS_KEY: raw.get(APP_SERVERS_KEY) or []}
    try:
        return MLEnvironment.model_validate(data)
    except ValidationError as error:
        fields = sorted(
            {
                ".".join(str(part) for part in issue["loc"])
                for issue in error.errors(include_input=False, include_context=False)
            },
        )
        message = f"Invalid environment in {path}: check {', '.join(fields)}."
    raise WrongParametersError(Formatter.escape(message))


def effective_config(
    path: Path,
    raw: dict,
) -> tuple[dict, list[dict]]:
    """Resolve an environment: root settings and app servers, defaults filled in.

    Parameters
    ----------
    path : Path
        Source filename, used only in validation diagnostics.
    raw : dict
        Settings already parsed by ``read_config``.

    Returns
    -------
    tuple[dict, list[dict]]
        Root settings and inherited server settings, including predefined
        servers. No-auth remains the explicit YAML ``app`` alias. Transport
        validation and authentication handler construction are deferred until
        a client is created, so incomplete connection setups can be inspected.

    Raises
    ------
    WrongParametersError
        If fields cannot be validated, without including their input values.
    """
    environment = _validate_environment(path, raw)
    root = environment.model_dump(
        mode="json",
        exclude={"app_servers"},
        by_alias=True,
        exclude_none=True,
    )
    if environment.auth is None:
        root["auth"] = "app"
    servers = [
        {
            "id": server.identifier,
            **_settings_values(environment.provide_config_dict(server.identifier)),
            "rest": server.rest,
        }
        for server in environment.app_servers
    ]
    return root, servers


def _settings_values(settings: dict) -> dict:
    """Serialize inherited settings, preserving no-auth as the YAML app alias."""
    values = {}
    for field, value in settings.items():
        if field == "auth" and value is None:
            values[field] = "app"
        elif isinstance(value, BaseModel):
            values[field] = value.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
        elif value is not None:
            values[field] = value
    return values


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
    return "password" in normalized or normalized in {"api_key", "token"}


def title(text: str) -> str:
    """Style a table title."""
    return f"<fg=magenta;options=bold>{Formatter.escape(text)}</>"


def header(text: str) -> str:
    """Style a table header cell."""
    return f"<fg=cyan;options=bold>{Formatter.escape(text)}</>"


def key(text: str) -> str:
    """Style a setting name cell."""
    return f"<fg=cyan>{Formatter.escape(text)}</>"
