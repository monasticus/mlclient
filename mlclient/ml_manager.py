"""The ML Manager module.

This module contains a high-level API for MarkLogic management.
It exports the following class:
    * MLManager
        A high-level class managing a MarkLogic instance.
"""
from __future__ import annotations

from mlclient import MLClient, MLConfiguration, MLResourcesClient
from mlclient.clients import LogsClient
from mlclient.exceptions import NotARestServerError, NoRestServerConfiguredError


class MLManager:
    """A high-level class managing a MarkLogic instance.

    It combines MLConfiguration and MLClient components to simplify every action
    to perform on your instance.
    """

    def __init__(
            self,
            environment_name: str,
    ):
        """Initialize MLManager instance.

        Parameters
        ----------
        environment_name :  str
            An MLClient configuration environment name.

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientEnvironmentNotFoundError
            If there's no .mlclient/mlclient-<environment_name>.yaml file
        """
        self._environment_name = environment_name
        self.config = MLConfiguration.from_environment(environment_name)

    @property
    def environment_name(
            self,
    ) -> str:
        """An MLClient configuration environment name.

        Returns
        -------
        str
            An MLClient configuration environment name.
        """
        return self._environment_name

    @property
    def config(
            self,
    ) -> MLConfiguration:
        """A MarkLogic configuration.

        Returns
        -------
        MLConfiguration
            A MarkLogic configuration
        """
        return self._config.model_copy(deep=True)

    @config.setter
    def config(
            self,
            ml_configuration: MLConfiguration,
    ):
        """Set a MarkLogic configuration.

        Parameters
        ----------
        ml_configuration : MLConfiguration
            A MarkLogic configuration
        """
        self._config = ml_configuration

    def get_client(
            self,
            app_server_id: str,
    ) -> MLClient:
        """Initialize an MLClient instance for a specific App Server.

        Parameters
        ----------
        app_server_id : str
            An App Server identifier

        Returns
        -------
        MLClient
            An MLClient instance
        """
        app_server_config = self.config.provide_config(app_server_id)
        return MLClient(**app_server_config)

    def get_resources_client(
            self,
            app_server_id: str | None = None,
    ) -> MLResourcesClient:
        """Initialize an MLResourcesClient instance for a specific App Server.

        If the no identifier is provided - it returns a client of a first configured
        REST server within an environment.

        Parameters
        ----------
        app_server_id : str | None, default None
            An App Server identifier

        Returns
        -------
        MLResourcesClient
            An MLResourcesClient instance

        Raises
        ------
        NotARestServerError
            If the App-Server identifier does not point to a REST server
        NoRestServerConfiguredError
            If an identifier has not been provided and there's no REST servers
            configured for the environment
        """
        if app_server_id is None:
            if len(self.config.rest_servers) == 0:
                env = self.environment_name
                msg = f"No REST server is configured for the [{env}] environment."
                raise NoRestServerConfiguredError(msg)
            app_server_id = self.config.rest_servers[0]
        elif app_server_id not in self.config.rest_servers:
            msg = f"[{app_server_id}] App-Server is not configured as a REST one."
            raise NotARestServerError(msg)
        app_server_config = self.config.provide_config(app_server_id)
        return MLResourcesClient(**app_server_config)

    def get_logs_client(
            self,
            app_server_id: str,
    ) -> LogsClient:
        """Initialize a LogsClient instance for a specific App Server.

        Parameters
        ----------
        app_server_id : str
            An App Server identifier

        Returns
        -------
        LogsClient
            An LogsClient instance
        """
        app_server_config = self.config.provide_config(app_server_id)
        return LogsClient(**app_server_config)
