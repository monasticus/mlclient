"""The ML Profile module.

This module contains an API for MarkLogic profile configuration.
It exports the following classes:

    * MLProfile
        A class representing a MarkLogic configuration profile.
    * MLServerConfig
        A class representing MarkLogic App Server configuration.
    * AuthMethod
        An enumeration class representing authorization methods.
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_serializer

from mlclient import constants
from mlclient.exceptions import (
    MLClientDirectoryNotFoundError,
    MLClientProfileNotFoundError,
    NoSuchAppServerError,
)

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """An enumeration class representing authorization methods."""

    BASIC = "basic"
    DIGEST = "digest"


class MLServerConfig(BaseModel):
    """A class representing MarkLogic App Server configuration."""

    identifier: str = Field(
        alias="id",
        description="A unique identifier of the App Server",
    )
    port: int = Field(description="A port number")
    auth_method: AuthMethod = Field(
        alias="auth",
        description="An authorization method",
        default=AuthMethod.DIGEST,
    )
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


class MLProfile(BaseModel):
    """A class representing a MarkLogic configuration profile."""

    app_name: str = Field(alias="app-name", description="An application name")
    protocol: str = Field(description="An HTTP protocol", default="http")
    host: str = Field(description="A hostname", default="localhost")
    username: str = Field(description="An username", default="admin")
    password: str = Field(description="A password", default="admin")
    app_servers: list[MLServerConfig] = Field(
        alias="app-servers",
        description="App Servers configurations' list",
        default=[MLServerConfig(id="manage", port=8002, rest=True)],
    )

    @property
    def rest_servers(
        self,
    ) -> list[str]:
        """REST servers identifiers."""
        return [
            app_server.identifier for app_server in self.app_servers if app_server.rest
        ]

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
        logger.debug("Getting configuration for the [%s] app server", app_server_id)
        ml_config = self.model_dump(exclude={"app_name", "app_servers"})
        app_server_gen = (
            app_server
            for app_server in self.app_servers
            if app_server.identifier == app_server_id
        )
        app_server = next(app_server_gen, None)
        if not app_server:
            msg = f"There's no [{app_server_id}] app server configuration!"
            raise NoSuchAppServerError(msg)
        app_server_config = app_server.model_dump(exclude={"identifier", "rest"})
        return {**ml_config, **app_server_config}

    @classmethod
    def load(
        cls,
        profile_name: str,
    ) -> MLProfile:
        """Instantiate MLProfile from a named profile.

        This method looks for a configuration file in the .mlclient directory.
        A profile configuration needs to match a file name pattern
        to be recognized: mlclient-<profile-name>.yaml.

        Parameters
        ----------
        profile_name : str
            A profile name

        Returns
        -------
        MLProfile
            An MLProfile instance

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientProfileNotFoundError
            If there's no .mlclient/mlclient-<profile_name>.yaml file
        """
        logger.debug(
            "Loading MLClient configuration for the profile: [%s]",
            profile_name,
        )
        pro_file_path = cls._find_mlclient_profile(profile_name)
        return cls.load_file(pro_file_path)

    @classmethod
    def load_file(
        cls,
        file_path: str,
    ) -> MLProfile:
        """Instantiate MLProfile from a file.

        Parameters
        ----------
        file_path : str
            A source configuration file

        Returns
        -------
        MLProfile
            An MLProfile instance
        """
        logger.info("Loading MLClient configuration from the file: [%s]", file_path)
        source_config = cls._get_source_config(file_path)
        return MLProfile(**source_config)

    @classmethod
    def _find_mlclient_profile(
        cls,
        profile_name: str,
    ) -> str:
        """Return MLClient profile configuration path.

        Parameters
        ----------
        profile_name : str
            An MLClient profile name

        Returns
        -------
        str
            An MLClient profile configuration path

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientProfileNotFoundError
            If there's no .mlclient/mlclient-<profile_name>.yaml file
        """
        ml_client_dir = cls._find_mlclient_directory(Path.cwd())
        pro_file_name = f"mlclient-{profile_name}.yaml"
        pro_file_path = next(Path(ml_client_dir).glob(pro_file_name), None)
        if not pro_file_path:
            msg = (
                f"MLClient's profile configuration has not been found for "
                f"[{profile_name}]!"
            )
            raise MLClientProfileNotFoundError(msg)
        logger.debug("MLClient configuration file found: [%s]", pro_file_name)
        return pro_file_path.as_posix()

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
            msg = (
                f"{constants.ML_CLIENT_DIR} directory has not been found in any of "
                f"parent directories!"
            )
            raise MLClientDirectoryNotFoundError(msg)
        mlclient_dir = next(
            (path for path in path.glob(constants.ML_CLIENT_DIR) if path.is_dir()),
            None,
        )
        if mlclient_dir:
            logger.debug(
                "MLClient configuration home directory found: [%s]",
                mlclient_dir,
            )
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
