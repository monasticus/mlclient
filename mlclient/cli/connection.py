"""Resolve CLI connection selectors without changing environment configuration."""

from __future__ import annotations

from mlclient import MLClient, MLClientManager
from mlclient.exceptions import WrongParametersError


_MAX_PORT = 65535

def get_client(manager: MLClientManager, connection: str | None) -> MLClient:
    """Create a client for a configured identifier or a numeric port.

    Parameters
    ----------
    manager : MLClientManager
        Manager for the selected environment.
    connection : str | None
        Configured identifier, TCP port (1-65535), or None for the default REST
        connection. A numeric port overrides the default connection's port.

    Returns
    -------
    MLClient
        Disconnected client retaining the environment's auxiliary API settings.

    Raises
    ------
    WrongParametersError
        If a numeric port is outside the TCP range.
    NoSuchAppServerError
        If an identifier is not configured.
    ConfigError
        If the resolved connection settings are incompatible.
    """
    if connection is not None and connection.isascii() and connection.isdecimal():
        port = int(connection)
        if not 1 <= port <= _MAX_PORT:
            msg = "Connection port must be between 1 and 65535."
            raise WrongParametersError(msg)
        return manager.get_client(port=port)
    return manager.get_client(connection)
