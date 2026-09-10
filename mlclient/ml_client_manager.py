"""The ML Client Manager module.

This module contains a high-level API for MarkLogic management.
It exports the following class:
    * MLClientManager
        A high-level class managing MarkLogic clients for a given environment.
"""

from __future__ import annotations

from mlclient.clients import AsyncHttpClient, AsyncMLClient, HttpClient, MLClient
from mlclient.clients.http_client import NO_RETRY_STRATEGY
from mlclient.connection import UNSET
from mlclient.exceptions import (
    NoRestServerConfiguredError,
    NoSuchAppServerError,
)
from mlclient.http_config import HEALTH_TIMEOUT, HTTPConfig
from mlclient.ml_environment import MLEnvironment


class MLClientManager:
    """A high-level class managing MarkLogic clients for a given environment.

    It combines MLEnvironment and MLClient components to simplify every action
    to perform on your instance.
    """

    def __init__(
        self,
        env_name: str,
        **overrides,
    ):
        """Load an environment and store HTTP defaults for clients created from it.

        The environment is loaded immediately. Overrides are applied and validated
        when a configuration or client is requested; constructing the manager does
        not open HTTP sessions.

        Parameters
        ----------
        env_name : str
            Environment name selecting .mlclient/mlclient-<env_name>.yaml.
            The .mlclient directory is located by searching from the current
            working directory through its parents.
        **overrides
            HTTPConfig.clone keyword arguments: protocol, host, port, auth,
            username, password, ssl, cloud, retry, limits and timeout. Applied
            to every server; per-call overrides take precedence. Retry and
            timeout are configured only in Python; an explicit strategy or
            timeout also applies to health. These defaults do not modify the
            environment file.

        Raises
        ------
        MLClientDirectoryNotFoundError
            If no .mlclient directory is found.
        MLClientEnvironmentNotFoundError
            If the named environment file is missing.
        OSError
            If the environment file cannot be read.
        yaml.YAMLError
            If the environment file contains invalid YAML.
        pydantic.ValidationError
            If the environment data fails model validation.
        """
        self._env_name = env_name
        self._overrides = overrides
        self.config = MLEnvironment.load(env_name)

    @property
    def env_name(
        self,
    ) -> str:
        """Return the name used to load this manager's environment.

        Returns
        -------
        str
            The original environment name. Replacing config does not change it.
        """
        return self._env_name

    @property
    def config(
        self,
    ) -> MLEnvironment:
        """Return a deep copy of the current environment configuration.

        Returns
        -------
        MLEnvironment
            An independent copy of the environment model. Mutating it does not
            change the manager unless it is assigned back through this property.
            Manager HTTP overrides, including retry, limits and timeout, are not
            part of this model.
        """
        return self._config.model_copy(deep=True)

    @config.setter
    def config(
        self,
        ml_configuration: MLEnvironment,
    ):
        """Replace the environment used for subsequent configuration requests.

        Parameters
        ----------
        ml_configuration : MLEnvironment
            The environment model to store. The supplied object is retained,
            not copied. This assignment does not change env_name, manager HTTP
            overrides, existing clients or the environment file.

        Returns
        -------
        None
            No value is returned.
        """
        self._config = ml_configuration

    def get_config(self, app_server_id: str, **overrides) -> HTTPConfig:
        """Resolve HTTP settings for one server without creating a client.

        An explicit retry strategy from the manager or this call is preserved.
        If no strategy is supplied, health uses NO_RETRY_STRATEGY and other
        servers use DEFAULT_RETRY_STRATEGY. Passing retry=None in this call
        restores the selected server's default, overriding a manager strategy.

        Retry and timeout resolve independently. Without an explicit timeout,
        health uses HEALTH_TIMEOUT and other servers use DEFAULT_TIMEOUT. A
        manager timeout applies to every server including health; timeout=None
        at any level disables every HTTP timeout, while timeout=UNSET in this
        call inherits the manager value rather than clearing it.

        Parameters
        ----------
        app_server_id : str
            A configured App Server identifier, including health, manage or admin.
            The identifier is required; the server need not be marked as REST.
        **overrides
            HTTPConfig.clone keyword arguments: protocol, host, port, auth,
            username, password, ssl, cloud, retry, limits and timeout. Values
            override manager defaults, which override environment settings.
            Cloud retains its gateway port even when a port override is
            supplied. Retry is a Python-only HTTP option, not an environment
            YAML setting.

        Returns
        -------
        HTTPConfig
            The resolved server configuration, including the effective retry
            strategy. No HTTP session is opened; the environment and defaults
            used by later calls are unchanged.

        Raises
        ------
        NoSuchAppServerError
            If the App Server identifier is not configured.
        ConfigError
            If connection and authentication settings are incompatible.
        TypeError
            If an override name or authentication descriptor type is unsupported.
        ValueError
            If configuration values or authentication parameters are invalid.
        ImportError
            If the selected authentication method requires an unavailable
            optional dependency.
        """
        config = self._config.provide_config(app_server_id)
        overrides = {**self._overrides, **_without_unset(overrides)}
        if overrides:
            config = config.clone(**overrides)
        if app_server_id == "health":
            config = _apply_health_defaults(config)
        return config

    def get_client(self, app_server_id: str | None = None, **overrides) -> MLClient:
        """Create a synchronous MarkLogic client for a configured App Server.

        The selected server is the primary HTTP endpoint. Selecting health,
        manage or admin makes its corresponding API share the primary settings
        and session. Per-call overrides affect only that server; auxiliary APIs
        for other servers retain their own environment and manager settings.

        An explicit retry strategy from the manager or this call is preserved.
        If no strategy is supplied, health uses NO_RETRY_STRATEGY and other
        servers use DEFAULT_RETRY_STRATEGY. Passing retry=None in this call
        restores the selected server's default, overriding a manager strategy.

        Parameters
        ----------
        app_server_id : str | None, default None
            A configured App Server identifier, including health, manage or admin.
            None selects the first REST server in environment order. An explicit
            identifier does not require the server to be marked as REST.
        **overrides
            HTTPConfig.clone keyword arguments: protocol, host, port, auth,
            username, password, ssl, cloud, retry, limits and timeout. Values
            override manager defaults, which override environment settings.
            Cloud retains its gateway port even when a port override is
            supplied. Retry is a Python-only HTTP option, not an environment
            YAML setting.

        Returns
        -------
        MLClient
            A new, disconnected client. Use with to manage its lifecycle:
            entering opens the primary session, auxiliary sessions open on first
            request, and exiting closes all opened sessions. Creating the client
            leaves the environment and later calls unchanged.

        Raises
        ------
        NoSuchAppServerError
            If the App Server identifier is not configured.
        ConfigError
            If connection and authentication settings are incompatible.
        TypeError
            If an override name or authentication descriptor type is unsupported.
        ValueError
            If configuration values or authentication parameters are invalid.
        ImportError
            If the selected authentication method requires an unavailable
            optional dependency.
        NoRestServerConfiguredError
            If no identifier is supplied and no REST server is configured.
        """
        return MLClient(**self._client_configs(app_server_id, **overrides))

    def get_async_client(
        self,
        app_server_id: str | None = None,
        **overrides,
    ) -> AsyncMLClient:
        """Create an asynchronous MarkLogic client for a configured App Server.

        The selected server is the primary HTTP endpoint. Selecting health,
        manage or admin makes its corresponding API share the primary settings
        and session. Per-call overrides affect only that server; auxiliary APIs
        for other servers retain their own environment and manager settings.

        An explicit retry strategy from the manager or this call is preserved.
        If no strategy is supplied, health uses NO_RETRY_STRATEGY and other
        servers use DEFAULT_RETRY_STRATEGY. Passing retry=None in this call
        restores the selected server's default, overriding a manager strategy.

        Parameters
        ----------
        app_server_id : str | None, default None
            A configured App Server identifier, including health, manage or admin.
            None selects the first REST server in environment order. An explicit
            identifier does not require the server to be marked as REST.
        **overrides
            HTTPConfig.clone keyword arguments: protocol, host, port, auth,
            username, password, ssl, cloud, retry, limits and timeout. Values
            override manager defaults, which override environment settings.
            Cloud retains its gateway port even when a port override is
            supplied. Retry is a Python-only HTTP option, not an environment
            YAML setting.

        Returns
        -------
        AsyncMLClient
            A new, disconnected client. Use async with to manage its lifecycle:
            entering opens the primary session, auxiliary sessions open on first
            request, and exiting closes all opened sessions. Creating the client
            leaves the environment and later calls unchanged.

        Raises
        ------
        NoSuchAppServerError
            If the App Server identifier is not configured.
        ConfigError
            If connection and authentication settings are incompatible.
        TypeError
            If an override name or authentication descriptor type is unsupported.
        ValueError
            If configuration values or authentication parameters are invalid.
        ImportError
            If the selected authentication method requires an unavailable
            optional dependency.
        NoRestServerConfiguredError
            If no identifier is supplied and no REST server is configured.
        """
        return AsyncMLClient(**self._client_configs(app_server_id, **overrides))

    def get_async_http_client(
        self,
        app_server_id: str,
        **overrides,
    ) -> AsyncHttpClient:
        """Create a raw asynchronous HTTP client for one configured server.

        All requests target the selected server; no auxiliary API clients are
        created. Overrides affect this returned client only.

        An explicit retry strategy from the manager or this call is preserved.
        If no strategy is supplied, health uses NO_RETRY_STRATEGY and other
        servers use DEFAULT_RETRY_STRATEGY. Passing retry=None in this call
        restores the selected server's default, overriding a manager strategy.

        Parameters
        ----------
        app_server_id : str
            A configured App Server identifier, including health, manage or admin.
            The identifier is required; the server need not be marked as REST.
        **overrides
            HTTPConfig.clone keyword arguments: protocol, host, port, auth,
            username, password, ssl, cloud, retry, limits and timeout. Values
            override manager defaults, which override environment settings.
            Cloud retains its gateway port even when a port override is
            supplied. Retry is a Python-only HTTP option, not an environment
            YAML setting.

        Returns
        -------
        AsyncHttpClient
            A new, disconnected HTTP client. Use async with to open a reusable
            session and close it on exit. Requests outside a connected lifecycle
            use short-lived sessions. The environment and subsequent calls are
            unchanged.

        Raises
        ------
        NoSuchAppServerError
            If the App Server identifier is not configured.
        ConfigError
            If connection and authentication settings are incompatible.
        TypeError
            If an override name or authentication descriptor type is unsupported.
        ValueError
            If configuration values or authentication parameters are invalid.
        ImportError
            If the selected authentication method requires an unavailable
            optional dependency.
        """
        return AsyncHttpClient(config=self.get_config(app_server_id, **overrides))

    def get_http_client(self, app_server_id: str, **overrides) -> HttpClient:
        """Create a raw synchronous HTTP client for one configured server.

        All requests target the selected server; no auxiliary API clients are
        created. Overrides affect this returned client only.

        An explicit retry strategy from the manager or this call is preserved.
        If no strategy is supplied, health uses NO_RETRY_STRATEGY and other
        servers use DEFAULT_RETRY_STRATEGY. Passing retry=None in this call
        restores the selected server's default, overriding a manager strategy.

        Parameters
        ----------
        app_server_id : str
            A configured App Server identifier, including health, manage or admin.
            The identifier is required; the server need not be marked as REST.
        **overrides
            HTTPConfig.clone keyword arguments: protocol, host, port, auth,
            username, password, ssl, cloud, retry, limits and timeout. Values
            override manager defaults, which override environment settings.
            Cloud retains its gateway port even when a port override is
            supplied. Retry is a Python-only HTTP option, not an environment
            YAML setting.

        Returns
        -------
        HttpClient
            A new, disconnected HTTP client. Use with to open a reusable
            session and close it on exit. Requests outside a connected lifecycle
            use short-lived sessions. The environment and subsequent calls are
            unchanged.

        Raises
        ------
        NoSuchAppServerError
            If the App Server identifier is not configured.
        ConfigError
            If connection and authentication settings are incompatible.
        TypeError
            If an override name or authentication descriptor type is unsupported.
        ValueError
            If configuration values or authentication parameters are invalid.
        ImportError
            If the selected authentication method requires an unavailable
            optional dependency.
        """
        return HttpClient(config=self.get_config(app_server_id, **overrides))

    def _client_configs(
        self,
        app_server_id: str | None,
        **overrides,
    ) -> dict[str, HTTPConfig]:
        """Build primary and auxiliary HTTP configurations for a MarkLogic client.

        Resolve the selected server once. If it is manage, admin or health,
        reuse that same configuration object for its auxiliary entry. Resolve
        the remaining auxiliary servers with manager defaults and without the
        selected server's per-call overrides. No HTTP sessions are opened.

        An explicit retry strategy from the manager or this call is preserved.
        If no strategy is supplied, health uses NO_RETRY_STRATEGY and other
        servers use DEFAULT_RETRY_STRATEGY. Passing retry=None in this call
        restores the selected server's default, overriding a manager strategy.

        Parameters
        ----------
        app_server_id : str | None
            A configured App Server identifier, including health, manage or admin.
            None selects the first REST server in environment order. An explicit
            identifier does not require the server to be marked as REST.
        **overrides
            HTTPConfig.clone keyword arguments: protocol, host, port, auth,
            username, password, ssl, cloud, retry, limits and timeout. Values
            override manager defaults, which override environment settings.
            Cloud retains its gateway port even when a port override is
            supplied. Retry is a Python-only HTTP option, not an environment
            YAML setting.

        Returns
        -------
        dict[str, HTTPConfig]
            Constructor arguments named config, manage_config, admin_config and
            health_config. Matching primary and auxiliary entries refer to the
            same configuration, allowing the client to reuse their HTTP session.

        Raises
        ------
        NoSuchAppServerError
            If the App Server identifier is not configured.
        ConfigError
            If connection and authentication settings are incompatible.
        TypeError
            If an override name or authentication descriptor type is unsupported.
        ValueError
            If configuration values or authentication parameters are invalid.
        ImportError
            If the selected authentication method requires an unavailable
            optional dependency.
        NoRestServerConfiguredError
            If no identifier is supplied and no REST server is configured.
        """
        app_server_id = self._get_app_server_id(app_server_id)
        primary = self.get_config(app_server_id, **overrides)
        configs = {"config": primary}
        for server_id in ("manage", "admin", "health"):
            configs[f"{server_id}_config"] = (
                primary if server_id == app_server_id else self.get_config(server_id)
            )
        return configs

    def _get_app_server_id(self, app_server_id: str | None) -> str:
        """Validate an explicit server identifier or select the first REST server.

        Parameters
        ----------
        app_server_id : str | None
            A configured App Server identifier, including health, manage or admin.
            None selects the first REST server in environment order. An explicit
            identifier does not require the server to be marked as REST.

        Returns
        -------
        str
            The explicit identifier if it exists, otherwise the first configured
            REST server identifier. Does not resolve HTTP settings or open a
            session.

        Raises
        ------
        NoSuchAppServerError
            If an explicit identifier is not configured.
        NoRestServerConfiguredError
            If no identifier is supplied and no REST server is configured.
        """
        if app_server_id is None:
            if not self._config.rest_servers:
                env = self.env_name
                msg = f"No REST server is configured for the [{env}] environment."
                raise NoRestServerConfiguredError(msg)
            return self._config.rest_servers[0]
        if app_server_id not in self._config.app_server_ids:
            msg = f"There's no [{app_server_id}] app server configuration!"
            raise NoSuchAppServerError(msg)
        return app_server_id


def _without_unset(overrides: dict) -> dict:
    """Drop UNSET-valued overrides so a per-call UNSET inherits the manager value."""
    return {key: value for key, value in overrides.items() if value is not UNSET}


def _apply_health_defaults(config: HTTPConfig) -> HTTPConfig:
    """Default health's unset retry and timeout independently of one another."""
    overrides = {}
    if not config.has_explicit_retry:
        overrides["retry"] = NO_RETRY_STRATEGY
    if not config.has_explicit_timeout:
        overrides["timeout"] = HEALTH_TIMEOUT
    return config.clone(**overrides) if overrides else config
