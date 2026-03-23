"""The ML Client Manager module.

This module contains a high-level API for MarkLogic management.
It exports the following class:
    * MLClientManager
        A high-level class managing MarkLogic clients for a given profile.
"""

from __future__ import annotations

import logging

from mlclient.clients import HttpClient, MLClient
from mlclient.exceptions import NoRestServerConfiguredError, NotARestServerError
from mlclient.ml_profile import MLProfile

logger = logging.getLogger(__name__)


class MLClientManager:
    """A high-level class managing MarkLogic clients for a given profile.

    It combines MLProfile and MLClient components to simplify every action
    to perform on your instance.
    """

    def __init__(
        self,
        profile_name: str,
    ):
        """Initialize MLClientManager instance.

        Parameters
        ----------
        profile_name :  str
            A profile name.

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientProfileNotFoundError
            If there's no .mlclient/mlclient-<profile_name>.yaml file
        """
        self._profile_name = profile_name
        self.config = MLProfile.load(profile_name)

    @property
    def profile_name(
        self,
    ) -> str:
        """A profile name."""
        return self._profile_name

    @property
    def config(
        self,
    ) -> MLProfile:
        """A MarkLogic configuration profile."""
        return self._config.model_copy(deep=True)

    @config.setter
    def config(
        self,
        ml_configuration: MLProfile,
    ):
        """Set a MarkLogic configuration profile."""
        self._config = ml_configuration

    def get_client(
        self,
        rest_server_id: str | None = None,
    ) -> MLClient:
        """Initialize an MLClient instance for a specific App Server.

        If no identifier is provided, returns a client for the first configured
        REST server within the profile.

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
            configured for the profile
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
            configured for the profile
        """
        logger.debug("Verifying the app server id [%s]", rest_server_id or "")
        if rest_server_id is None:
            logger.debug("No id provided - trying to identify any REST app server")
            if len(self.config.rest_servers) == 0:
                profile = self.profile_name
                msg = f"No REST server is configured for the [{profile}] profile."
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
