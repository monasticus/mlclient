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
from mlclient.exceptions import (MLClientDirectoryNotFoundError,
                                 MLClientEnvironmentNotFoundError,
                                 NoSuchAppServerError)


class AuthMethod(Enum):
    """An enumeration class representing authorization methods."""

    BASIC = "basic"
    DIGEST = "digest"


class MLAppServerConfiguration(BaseModel):
    """A class representing MarkLogic App Server configuration."""

    identifier: str = Field(
        alias="id",
        description="A unique identifier of the App Server")
    port: int = Field(
        description="A port number")
    auth_method: AuthMethod = Field(
        alias="auth",
        description="An authorization method",
        default=AuthMethod.DIGEST)
    rest: bool = Field(
        description="A flag informing if the App-Server is a REST server",
        default=False,
    )

    @field_serializer("auth_method")
    def serialize_auth(
            self,
            auth_method: AuthMethod,
            _info,
    ):
        """Serialize auth field."""
        return auth_method.value


class MLConfiguration(BaseModel):
    """A class representing MarkLogic configuration."""

    app_name: str = Field(
        alias="app-name",
        description="An application name")
    protocol: str = Field(
        description="An HTTP protocol",
        default="http")
    host: str = Field(
        description="A hostname",
        default="localhost")
    username: str = Field(
        description="An username",
        default="admin")
    password: str = Field(
        description="A password",
        default="admin")
    app_servers: List[MLAppServerConfiguration] = Field(
        alias="app-servers",
        description="App Servers configurations' list",
        default=[MLAppServerConfiguration(id="manage", port=8002, rest=True)])

    @property
    def rest_servers(
            self,
    ) -> list[str]:
        """REST servers identifiers."""
        return [app_server.identifier
                for app_server in self.app_servers
                if app_server.rest]

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
        app_server_config = app_server.model_dump(exclude={"identifier", "rest"})
        return {**ml_config, **app_server_config}

    @classmethod
    def from_environment(
            cls,
            environment_name: str,
    ) -> MLConfiguration:
        """Instantiate MLConfiguration from an environment.

        This method looks for a configuration file in the .mlclient directory.
        An environment configuration needs to match a file name pattern
        to be recognized: mlclient-<environment-name>.yaml.

        Parameters
        ----------
        environment_name : str
            An MLClient environment name

        Returns
        -------
        MLConfiguration
            An MLConfiguration instance

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientEnvironmentNotFoundError
            If there's no .mlclient/mlclient-<environment_name>.yaml file
        """
        env_file_path = cls._find_mlclient_environment(environment_name)
        return cls.from_file(env_file_path)

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

    @classmethod
    def _find_mlclient_environment(
            cls,
            environment_name: str,
    ) -> str:
        """Return MLClient environment configuration path.

        Parameters
        ----------
        environment_name : str
            An MLClient environment name

        Returns
        -------
        str
            An MLClient environment configuration path

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientEnvironmentNotFoundError
            If there's no .mlclient/mlclient-<environment_name>.yaml file
        """
        ml_client_dir = cls._find_mlclient_directory(Path.cwd())
        env_file_name = f"mlclient-{environment_name}.yaml"
        env_file_path = next(Path(ml_client_dir).glob(env_file_name), None)
        if not env_file_path:
            msg = (f"MLClient's configuration has not been found for the environment "
                   f"[{environment_name}]!")
            raise MLClientEnvironmentNotFoundError(msg)
        return env_file_path.as_posix()

    @classmethod
    def _find_mlclient_directory(
            cls,
            path: Path,
    ) -> str:
        """Return MLClient configuration path.

        Recursively searches for .mlclient directory. If it is not being found,
        it tries in a parent until it reaches root dir.

        Parameters
        ----------
        path : Path
            A path to look for .mlclient subdirectory

        Returns
        -------
        str
            An MLClient configuration path

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        """
        if Path.as_posix(path) in (".", "/"):
            msg = (f"{constants.ML_CLIENT_DIR} directory has not been found in any of "
                   f"parent directories!")
            raise MLClientDirectoryNotFoundError(msg)
        mlclient_dir = next((
            path
            for path in path.glob(constants.ML_CLIENT_DIR)
            if path.is_dir()), None)
        if mlclient_dir:
            return mlclient_dir.as_posix()
        return cls._find_mlclient_directory(path.parent)

    @staticmethod
    def _get_source_config(
            file_path: str,
    ) -> dict:
        """Load a source MLClient's configuration YAML file.

        Parameters
        ----------
        file_path : str
            A source configuration's filepath

        Returns
        -------
        dict
            A source MLClient's configuration
        """
        with Path(file_path).open() as config_file:
            return yaml.safe_load(config_file.read())

