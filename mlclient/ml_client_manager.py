"""The ML Client Manager module.

This module contains a high-level API for MarkLogic management.
It exports the following class:
    * MLClientManager
        A high-level class managing MarkLogic clients for a given environment.
"""

from __future__ import annotations

import logging

from mlclient.clients import HttpClient, MLClient
from mlclient.exceptions import NoRestServerConfiguredError, NotARestServerError
from mlclient.ml_environment import MLEnvironment

logger = logging.getLogger(__name__)


class MLClientManager:
    """A high-level class managing MarkLogic clients for a given environment.

    It combines MLEnvironment and MLClient components to simplify every action
    to perform on your instance.
    """

    def __init__(
        self,
        env_name: str,
    ):
        """Initialize MLClientManager instance.

        Parameters
        ----------
        env_name :  str
            An environment name.

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientEnvironmentNotFoundError
            If there's no .mlclient/mlclient-<env_name>.yaml file
        """
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

    def get_client(
        self,
        rest_server_id: str | None = None,
    ) -> MLClient:
        """Initialize an MLClient instance for a specific App Server.

        If no identifier is provided, returns a client for the first configured
        REST server within the environment.

        Parameters
        ----------
        rest_server_id : str | None, default None
            A REST App Server identifier

        Returns
        -------
        MLClient
            An MLClient instance

        Raises
        ------
        NotARestServerError
            If the App-Server identifier does not point to a REST server
            (only when rest_server_id is not None and is not a REST server)
        NoRestServerConfiguredError
            If an identifier has not been provided and there's no REST servers
            configured for the environment
        """
        rest_server_id = self._get_rest_server_id(rest_server_id)
        app_server_config = self.config.provide_config(rest_server_id)
        return MLClient(**app_server_config)

    def get_http_client(
        self,
        app_server_id: str,
    ) -> HttpClient:
        """Initialize an HttpClient instance for a specific App Server.

        Parameters
        ----------
        app_server_id : str
            An App Server identifier

        Returns
        -------
        HttpClient
            An HttpClient instance
        """
        app_server_config = self.config.provide_config(app_server_id)
        return HttpClient(**app_server_config)

    def _get_rest_server_id(
        self,
        rest_server_id: str | None = None,
    ) -> str:
        """Return verified REST Server identifier.

        Parameters
        ----------
        rest_server_id : str | None, default None
            A REST App Server identifier

        Returns
        -------
        str
            A REST server identifier

        Raises
        ------
        NotARestServerError
            If the App-Server identifier does not point to a REST server
        NoRestServerConfiguredError
            If an identifier has not been provided and there's no REST servers
            configured for the environment
        """
        logger.debug("Verifying the app server id [%s]", rest_server_id or "")
        if rest_server_id is None:
            logger.debug("No id provided - trying to identify any REST app server")
            if len(self.config.rest_servers) == 0:
                env = self.env_name
                msg = f"No REST server is configured for the [{env}] environment."
                raise NoRestServerConfiguredError(msg)
            rest_server_id = self.config.rest_servers[0]
            logger.debug("Identified REST app server id: [%s]", rest_server_id)
            return rest_server_id
        if rest_server_id not in self.config.rest_servers:
            msg = f"[{rest_server_id}] App-Server is not configured as a REST one."
            raise NotARestServerError(msg)
        logger.debug(
            "The [%s] app server has been verified as a REST one.",
            rest_server_id,
        )
        return rest_server_id
