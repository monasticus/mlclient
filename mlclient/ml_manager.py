"""The ML Manager module.

This module contains a high-level API for MarkLogic management.
It exports the following class:
    * MLManager
        A high-level class managing a MarkLogic instance.
"""
from __future__ import annotations

from mlclient import MLClient, MLConfiguration, MLResourceClient


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

    def get_resource_client(
            self,
            app_server_id: str,
    ) -> MLResourceClient:
        """Initialize an MLResourceClient instance for a specific App Server.

        Parameters
        ----------
        app_server_id : str
            An App Server identifier

        Returns
        -------
        MLResourceClient
            An MLResourceClient instance
        """
        app_server_config = self.config.provide_config(app_server_id)
        return MLResourceClient(**app_server_config)
