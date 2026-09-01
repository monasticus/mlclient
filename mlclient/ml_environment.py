"""The ML Environment module.

This module contains an API for MarkLogic environment configuration.
It exports the following classes:

    * MLEnvironment
        A class representing a MarkLogic configuration environment.
    * MLServerConfig
        A class representing MarkLogic App Server configuration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

import yaml
from pydantic import BaseModel, Field, model_validator

from mlclient import constants
from mlclient.auth import AuthConfig
from mlclient.connection import CloudConfig, SSLConfig
from mlclient.exceptions import (
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
    NoSuchAppServerError,
)
from mlclient.http_config import HTTPConfig

logger = logging.getLogger(__name__)

Auth = Union[str, AuthConfig]


class MLServerConfig(BaseModel):
    """A class representing MarkLogic App Server configuration.

    Connection and authentication settings default to ``None`` so an unset
    field inherits the root-level value from MLEnvironment.
    """

    identifier: str = Field(
        alias="id",
        description="A unique identifier of the App Server",
    )
    port: Optional[int] = Field(
        description="A port number; None uses the connection's default port",
        default=None,
    )
    protocol: Optional[str] = Field(
        description="An HTTP protocol; None inherits from root",
        default=None,
    )
    auth: Optional[Auth] = Field(
        description="An authentication method; None inherits from root",
        default=None,
    )
    username: Optional[str] = Field(
        description="A username; None inherits from root",
        default=None,
    )
    password: Optional[str] = Field(
        description="A password; None inherits from root",
        default=None,
    )
    ssl: Optional[SSLConfig] = Field(
        description="SSL/TLS configuration; None inherits from root",
        default=None,
    )
    rest: bool = Field(
        description="A flag informing if the App-Server is a REST server",
        default=False,
    )


_DEFAULT_APP_SERVERS = [
    MLServerConfig(id="app-services", rest=True),
    MLServerConfig(id="manage", port=8002),
    MLServerConfig(id="admin", port=8001),
]


class MLEnvironment(BaseModel):
    """A class representing a MarkLogic configuration environment.

    Connection and authentication settings configured here act as defaults for
    every app server and may be overridden per server. The App Services, Manage
    and Admin servers always exist; a user entry sharing one of their ids
    overrides it.
    """

    app_name: Optional[str] = Field(
        alias="app-name",
        description="An application name; a label used to scope discovery when set",
        default=None,
    )
    protocol: str = Field(description="An HTTP protocol", default="http")
    host: str = Field(description="A hostname", default="localhost")
    username: str = Field(description="An username", default="admin")
    password: str = Field(description="A password", default="admin")
    auth: Auth = Field(description="An authentication method", default="digest")
    ssl: Optional[SSLConfig] = Field(
        description="SSL/TLS configuration",
        default=None,
    )
    cloud: Optional[CloudConfig] = Field(
        description="MarkLogic Cloud configuration",
        default=None,
    )
    app_servers: list[MLServerConfig] = Field(
        alias="app-servers",
        description="App Servers configurations' list",
        default_factory=lambda: [s.model_copy() for s in _DEFAULT_APP_SERVERS],
    )

    @model_validator(mode="after")
    def _ensure_default_app_servers(self) -> MLEnvironment:
        """Guarantee the App Services, Manage and Admin servers always exist.

        User entries keep their position and win on id collision; any default
        the user did not define is appended, copied so environments never share
        a server instance.
        """
        by_id = {server.identifier: server for server in self.app_servers}
        for default in _DEFAULT_APP_SERVERS:
            by_id.setdefault(default.identifier, default.model_copy())
        self.app_servers = list(by_id.values())
        return self

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
    ) -> HTTPConfig:
        """Provide a resolved connection configuration for an App Server.

        The root-level connection and auth defaults are merged with the app
        server's overrides and resolved into an HTTPConfig ready to hand to a
        client via its ``config`` parameter.

        Parameters
        ----------
        app_server_id : str
            A unique identifier of the App Server

        Returns
        -------
        HTTPConfig
            A resolved configuration for a client initialization
        """
        logger.debug("Getting configuration for the [%s] app server", app_server_id)
        ml_config = self._root_config()
        app_server = self._find_app_server(app_server_id)
        app_server_config = self._app_server_overrides(app_server)
        merged = {**ml_config, **app_server_config}
        if app_server.ssl is not None:
            merged["ssl"] = self._merge_ssl(self.ssl, app_server.ssl)
        return HTTPConfig.resolve(**merged)

    def _root_config(self) -> dict:
        """Return root-level connection and auth defaults.

        A Cloud environment omits protocol and auth: Cloud forces HTTPS and
        handles authentication via its API key, so passing the defaults would
        conflict with the Cloud connection's enforced invariants.
        """
        if self.cloud is not None:
            return {"host": self.host, "cloud": self.cloud}
        return {
            "protocol": self.protocol,
            "host": self.host,
            "username": self.username,
            "password": self.password,
            "auth": self.auth,
            "ssl": self.ssl,
            "cloud": None,
        }

    def _find_app_server(
        self,
        app_server_id: str,
    ) -> MLServerConfig:
        """Return the app server with the given id, or raise."""
        app_server = next(
            (
                app_server
                for app_server in self.app_servers
                if app_server.identifier == app_server_id
            ),
            None,
        )
        if not app_server:
            msg = f"There's no [{app_server_id}] app server configuration!"
            raise NoSuchAppServerError(msg)
        return app_server

    @staticmethod
    def _app_server_overrides(
        app_server: MLServerConfig,
    ) -> dict:
        """Return non-None app server fields that override root defaults."""
        overrides = {
            "port": app_server.port,
            "protocol": app_server.protocol,
            "auth": app_server.auth,
            "username": app_server.username,
            "password": app_server.password,
            "ssl": app_server.ssl,
        }
        return {key: value for key, value in overrides.items() if value is not None}

    @staticmethod
    def _merge_ssl(
        root_ssl: SSLConfig | None,
        server_ssl: SSLConfig,
    ) -> SSLConfig:
        """Merge a server's SSL settings onto the root's, field by field.

        Unlike the other settings, which a server replaces wholesale, SSL merges
        so a server declaring only a client certificate keeps the root's server
        verification (its CA bundle). Only fields the server set explicitly
        override the root; ``model_fields_set`` distinguishes an explicit
        ``verify: false`` from an unset field left at its default.
        """
        if root_ssl is None:
            return server_ssl
        overrides = {
            field: getattr(server_ssl, field) for field in server_ssl.model_fields_set
        }
        return root_ssl.model_copy(update=overrides)

    @classmethod
    def load(
        cls,
        env_name: str,
    ) -> MLEnvironment:
        """Instantiate MLEnvironment from a named environment.

        This method looks for a configuration file in the .mlclient directory.
        An environment configuration needs to match a file name pattern
        to be recognized: mlclient-<env-name>.yaml.

        Parameters
        ----------
        env_name : str
            An environment name

        Returns
        -------
        MLEnvironment
            An MLEnvironment instance

        Raises
        ------
        MLClientDirectoryNotFoundError
            If .mlclient directory has not been found
        MLClientEnvironmentNotFoundError
            If there's no .mlclient/mlclient-<env_name>.yaml file
        """
        logger.debug(
            "Loading MLClient configuration for the environment: [%s]",
            env_name,
        )
        env_file_path = cls._find_mlclient_environment(env_name)
        return cls.load_file(env_file_path)

    @classmethod
    def load_file(
        cls,
        file_path: str,
    ) -> MLEnvironment:
        """Instantiate MLEnvironment from a file.

        Parameters
        ----------
        file_path : str
            A source configuration file

        Returns
        -------
        MLEnvironment
            An MLEnvironment instance
        """
        logger.info("Loading MLClient configuration from the file: [%s]", file_path)
        source_config = cls._get_source_config(file_path)
        return MLEnvironment(**source_config)

    @classmethod
    def _find_mlclient_environment(
        cls,
        env_name: str,
    ) -> str:
        """Return MLClient environment configuration path.

        Parameters
        ----------
        env_name : str
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
            If there's no .mlclient/mlclient-<env_name>.yaml file
        """
        ml_client_dir = cls._find_mlclient_directory(Path.cwd())
        env_file_name = f"mlclient-{env_name}.yaml"
        env_file_path = next(Path(ml_client_dir).glob(env_file_name), None)
        if not env_file_path:
            msg = (
                f"MLClient's environment configuration has not been found for "
                f"[{env_name}]!"
            )
            raise MLClientEnvironmentNotFoundError(msg)
        logger.debug("MLClient configuration file found: [%s]", env_file_name)
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
