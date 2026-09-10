"""The ML Client Manager module.

This module contains a high-level API for MarkLogic management.
It exports the following class:
    * MLClientManager
        A high-level class managing MarkLogic clients for a given environment.
"""

from __future__ import annotations

from mlclient.clients import AsyncHttpClient, AsyncMLClient, HttpClient, MLClient
from mlclient.clients.http_client import NO_RETRY_STRATEGY
from mlclient.exceptions import (
    NoRestServerConfiguredError,
    NoSuchAppServerError,
)
from mlclient.http_config import HTTPConfig
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
        """Initialize MLClientManager instance.

        Parameters
        ----------
        env_name :  str
            An environment name.
        **overrides
            HTTPConfig.clone parameters applied to every server. Per-call
            overrides take precedence. Environment configuration is unchanged.

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientEnvironmentNotFoundError
            If there's no .mlclient/mlclient-<env_name>.yaml file
        """
        self._overrides = overrides
        self._env_name = env_name
        self.config = MLEnvironment.load(env_name)

    @property
    def env_name(
        self,
    ) -> str:
        """An environment name."""
        return self._env_name

    @property
    def config(
        self,
    ) -> MLEnvironment:
        """A MarkLogic configuration environment."""
        return self._config.model_copy(deep=True)

    @config.setter
    def config(
        self,
        ml_configuration: MLEnvironment,
    ):
        """Set a MarkLogic configuration environment."""
        self._config = ml_configuration

    def get_config(self, app_server_id: str, **overrides) -> HTTPConfig:
        """Resolve a server's HTTP settings without creating a client.

        Precedence: environment, manager overrides, then per-call overrides.
        Accepts HTTPConfig.clone parameters, including retry. An unspecified
        retry (None) uses no retries for health and the ordinary default for
        other servers. Unknown parameters raise TypeError.
        """
        config = self._config.provide_config(app_server_id)
        overrides = {**self._overrides, **overrides}
        if overrides:
            config = config.clone(**overrides)
        if app_server_id == "health" and not config.has_explicit_retry:
            return config.clone(retry=NO_RETRY_STRATEGY)
        return config

    def get_client(self, app_server_id: str | None = None, **overrides) -> MLClient:
        """Initialize a client for any named App Server.

        Parameters
        ----------
        app_server_id : str | None, default None
            An App Server identifier, including health, manage or admin.
            Omit to select the first REST server in the environment.
        **overrides
            HTTPConfig.clone parameters for the selected server only. When
            selecting manage, admin or health, its corresponding API uses the
            same settings and HTTP session. Other APIs retain manager defaults.

        Returns
        -------
        MLClient
            A disconnected client; use it as a context manager for session reuse.

        Raises
        ------
        NoSuchAppServerError
            If the identifier is not configured.
        NoRestServerConfiguredError
            If no identifier is supplied and no REST server is configured.
        """
        return MLClient(**self._client_configs(app_server_id, **overrides))

    def get_async_client(
        self,
        app_server_id: str | None = None,
        **overrides,
    ) -> AsyncMLClient:
        """Async counterpart of get_client, with identical configuration rules."""
        return AsyncMLClient(**self._client_configs(app_server_id, **overrides))

    def get_async_http_client(
        self,
        app_server_id: str,
        **overrides,
    ) -> AsyncHttpClient:
        """Create a raw async client using get_config's defaults and overrides."""
        return AsyncHttpClient(config=self.get_config(app_server_id, **overrides))

    def get_http_client(self, app_server_id: str, **overrides) -> HttpClient:
        """Create a raw client using get_config's defaults and overrides."""
        return HttpClient(config=self.get_config(app_server_id, **overrides))

    def _client_configs(
        self,
        app_server_id: str | None,
        **overrides,
    ) -> dict[str, HTTPConfig]:
        app_server_id = self._get_app_server_id(app_server_id)
        primary = self.get_config(app_server_id, **overrides)
        configs = {"config": primary}
        for server_id in ("manage", "admin", "health"):
            configs[f"{server_id}_config"] = (
                primary if server_id == app_server_id else self.get_config(server_id)
            )
        return configs

    def _get_app_server_id(self, app_server_id: str | None) -> str:
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
