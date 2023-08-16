"""The ML Configuration module.

This module contains an API for MarkLogic configuration.
It exports the following classes:
    * MLConfiguration
        A class representing MarkLogic configuration.
    * MLAppServerConfiguration
        A class representing MarkLogic App Server configuration.
    * AuthMethod
        An enumeration class representing authorization methods.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field, field_serializer

from mlclient import constants
from mlclient.exceptions import NoSuchAppServerError


class AuthMethod(Enum):
    """An enumeration class representing authorization methods."""

    BASIC = "basic"
    DIGEST = "digest"


class MLAppServerConfiguration(BaseModel):
    """A class representing MarkLogic App Server configuration.

    Attributes
    ----------
    identifier : str
        A unique identifier of the App Server
    port : int
        A port number
    auth : AuthMethod
        An authorization method
    """

    identifier: str = Field(
        alias="id")
    port: int
    auth: AuthMethod = AuthMethod.DIGEST

    @field_serializer("auth")
    def serialize_auth(
            self,
            auth: AuthMethod,
            _info,
    ):
        """Serialize auth field."""
        return auth.value


class MLConfiguration(BaseModel):
    """A class representing MarkLogic configuration.

    Attributes
    ----------
    app_name : str
        An application name
    protocol : str
        An HTTP protocol
    host : str
        A hostname
    username : str
        An username
    password : str
        A password
    app_servers : List[MLAppServerConfiguration]
        App Servers configurations' list
    """

    app_name: str = Field(
        alias="app-name")
    protocol: str = "http"
    host: str = "localhost"
    username: str = "admin"
    password: str = "admin"
    app_servers: List[MLAppServerConfiguration] = Field(
        alias="app-servers",
        default=[MLAppServerConfiguration(id="manage", port=8002)])

    def provide_config(
            self,
            app_server_id: str,
    ) -> dict:
        """Provide an app server configuration for MLClient's use.

        Parameters
        ----------
        app_server_id : str
            A unique identifier of the App Server

        Returns
        -------
        dict
            A configuration dictionary for an MLClient initialization
        """
        ml_config = self.model_dump(exclude={"app_name", "app_servers"})
        app_server = next((app_server
                           for app_server in self.app_servers
                           if app_server.identifier == app_server_id), None)
        if not app_server:
            msg = f"There's no [{app_server_id}] app server configuration!"
            raise NoSuchAppServerError(msg)
        app_server_config = app_server.model_dump(exclude={"identifier"})
        return {**ml_config, **app_server_config}

    @classmethod
    def from_environment(
            cls,
            environment_name: str,
    ):
        """Instantiate MLConfiguration from an environment.

        This method looks for a configuration file in the .mlclient directory.
        An environment configuration needs to match a file name pattern
        to be recognized: mlclient-<environment-name>.yaml.

        Parameters
        ----------
        environment_name : str
            An environment name

        Returns
        -------
        MLConfiguration
            An MLConfiguration instance
        """
        file_path = f"{constants.ML_CLIENT_PATH}/mlclient-{environment_name}.yaml"
        return cls.from_file(file_path)

    @classmethod
    def from_file(
            cls,
            file_path: str,
    ) -> MLConfiguration:
        """Instantiate MLConfiguration from a file.

        Parameters
        ----------
        file_path : str
            A source configuration file

        Returns
        -------
        MLConfiguration
            An MLConfiguration instance
        """
        source_config = cls._get_source_config(file_path)
        return MLConfiguration(**source_config)

    @staticmethod
    def _get_source_config(
            file_path: str,
    ):
        with Path(file_path).open() as config_file:
            return yaml.safe_load(config_file.read())
