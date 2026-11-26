"""The ML Environment module.

This module contains an API for MarkLogic environment configuration.
It exports the following classes:

    * MLEnvironment
        A class representing a MarkLogic configuration environment.
    * MLServerConfig
        A class representing MarkLogic App Server configuration.

It exports the following functions:

    * find_mlclient_environment
        Locate a named environment's configuration file in the nearest .mlclient.
    * find_mlclient_directory
        Locate the nearest .mlclient directory at a path or in an ancestor.

It exports the following values:

    * DEFAULT_APP_SERVER_SETTINGS
        The App Services, Manage, Admin and Health servers present in every
        environment.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Optional, Union, cast

import yaml
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    model_validator,
)

from mlclient import _constants as constants
from mlclient.auth import AuthConfig, require_known_auth_shortcut
from mlclient.connection import (
    CLOUD_PORT,
    CLOUD_PROTOCOL,
    DEFAULT_PORT,
    MARKLOGIC_ADMIN_PORT,
    MARKLOGIC_HEALTHCHECK_PORT,
    MARKLOGIC_MANAGE_PORT,
    CloudConfig,
    SSLConfig,
    secret_value,
)
from mlclient.exceptions import (
    ConfigError,
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
    NoSuchAppServerError,
)
from mlclient.http import HTTPConfig

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails

    from mlclient._typing import HTTPConfigOverrides

logger = logging.getLogger(__name__)


def _validate_auth(value: object) -> object:
    """Resolve the app alias to no HTTP auth and validate the setting eagerly.

    A mapping is validated as an AuthConfig here rather than by the union, so a
    mistake in it is reported once under ``auth`` instead of once per union
    member.
    """
    if value == "app":
        return None
    if isinstance(value, str):
        require_known_auth_shortcut(value)
    if isinstance(value, dict):
        return AuthConfig.model_validate(value)
    return value


Auth = Annotated[
    Optional[Union[str, AuthConfig]],
    BeforeValidator(_validate_auth),
]


class MLServerConfig(BaseModel):
    """A class representing MarkLogic App Server configuration.

    Connection and authentication settings default to ``None`` so an unset
    field inherits the root-level value from MLEnvironment. Unknown settings
    are rejected, assignments are validated too, and ``password`` is a
    ``SecretStr`` (a plain str assigned to it is wrapped).
    """

    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        validate_assignment=True,
    )

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
    auth: Auth = Field(
        description="An authentication method; omitted inherits from root",
        default=None,
    )
    username: Optional[str] = Field(
        description="A username; None inherits from root",
        default=None,
    )
    password: Optional[SecretStr] = Field(
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


DEFAULT_APP_SERVER_SETTINGS = (
    {"id": "app-services", "rest": True},
    {"id": "manage", "port": MARKLOGIC_MANAGE_PORT},
    {"id": "admin", "port": MARKLOGIC_ADMIN_PORT},
    {"id": "health", "port": MARKLOGIC_HEALTHCHECK_PORT, "auth": "app"},
)


_DEFAULT_APP_SERVERS = [
    MLServerConfig.model_validate(server) for server in DEFAULT_APP_SERVER_SETTINGS
]


class MLEnvironment(BaseModel):
    """A class representing a MarkLogic configuration environment.

    Connection and authentication settings configured here act as defaults for
    every app server and may be overridden per server. The App Services, Manage,
    Admin and Health servers always exist; a user entry sharing one of their ids
    overrides it. Unknown settings are rejected, assignments are validated too,
    and ``password`` is a ``SecretStr`` (a plain str assigned to it is wrapped).
    """

    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        validate_assignment=True,
    )

    app_name: Optional[str] = Field(
        alias="app-name",
        description="An application name; a label used to scope discovery when set",
        default=None,
    )
    protocol: str = Field(description="An HTTP protocol", default="http")
    host: str = Field(description="A hostname", default="localhost")
    username: str = Field(description="An username", default="admin")
    password: SecretStr = Field(description="A password", default=SecretStr("admin"))
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
        """Guarantee the App Services, Manage, Admin and Health servers exist.

        User entries keep their position and win on id collision; any default
        the user did not define is appended, copied so environments never share
        a server instance.
        """
        by_id = {server.identifier: server for server in self.app_servers}
        for default in _DEFAULT_APP_SERVERS:
            by_id.setdefault(default.identifier, default.model_copy())
        merged_app_servers = list(by_id.values())
        # Assignment is validated and runs this validator again: assigning only
        # a changed list ends that recursion after one round.
        if merged_app_servers != self.app_servers:
            self.app_servers = merged_app_servers
        return self

    @property
    def app_server_ids(
        self,
    ) -> list[str]:
        """App server identifiers."""
        return [app_server.identifier for app_server in self.app_servers]

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
        """Provide an App Server's inherited connection settings as an HTTPConfig.

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
        return HTTPConfig.resolve(
            **cast("HTTPConfigOverrides", self.provide_config_dict(app_server_id)),
        )

    def provide_config_dict(self, app_server_id: str) -> dict[str, object]:
        """Provide an App Server's inherited connection settings as a dictionary.

        Merge root settings with server overrides, including fieldwise SSL
        inheritance and default ports. Unlike ``provide_config``, this method
        does not construct authentication handlers or validate transport/auth
        combinations. It can inspect Kerberos and certificate settings without
        optional dependencies or locally installed certificates.

        Parameters
        ----------
        app_server_id : str
            The environment's App Server identifier.

        Returns
        -------
        dict
            Independent keyword arguments for ``HTTPConfig.resolve``, including
            copies of nested models. Explicit ``auth=None`` is preserved.
            Invalid transport combinations remain inspectable and
            are rejected when ``provide_config`` constructs the configuration.

        Raises
        ------
        NoSuchAppServerError
            If the environment does not contain this identifier.
        """
        ml_config = self._root_config()
        app_server = self._find_app_server(app_server_id)
        app_server_config = self._app_server_overrides(app_server)
        merged = {
            **ml_config,
            **app_server_config,
            "port": self._effective_port(app_server),
        }
        if app_server.ssl is not None:
            merged["ssl"] = self._merge_ssl(self.ssl, app_server.ssl)
        if self.cloud is not None:
            merged.setdefault("protocol", CLOUD_PROTOCOL)
            merged.setdefault("auth", None)
        return deepcopy(merged)

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
            "password": self.password.get_secret_value(),
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
            raise no_such_app_server_error(self, app_server_id)
        return app_server

    def _effective_port(
        self,
        app_server: MLServerConfig,
    ) -> int:
        """Return the server's port, or the connection's default when unset."""
        if app_server.port is not None:
            return app_server.port
        return CLOUD_PORT if self.cloud is not None else DEFAULT_PORT

    @staticmethod
    def _app_server_overrides(
        app_server: MLServerConfig,
    ) -> dict:
        """Return app server fields that override root defaults."""
        overrides: dict = {
            "protocol": app_server.protocol,
            "username": app_server.username,
            "password": secret_value(app_server.password),
            "ssl": app_server.ssl,
        }
        overrides = {
            key: value for key, value in overrides.items() if value is not None
        }
        if "auth" in app_server.model_fields_set:
            overrides["auth"] = app_server.auth
        return overrides

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
        overrides: dict = {
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
        ConfigError
            If the file is empty, is not a YAML mapping or holds invalid settings
        """
        logger.debug(
            "Loading MLClient configuration for the environment: [%s]",
            env_name,
        )
        env_file_path = find_mlclient_environment(env_name)
        return cls.load_file(env_file_path.as_posix())

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

        Raises
        ------
        ConfigError
            If the file is empty, is not a YAML mapping or holds invalid
            settings. The message names the file and lists one problem per
            line, without the configured values.
        """
        logger.info("Loading MLClient configuration from the file: [%s]", file_path)
        source_config = cls._get_source_config(file_path)
        try:
            return cls.model_validate(source_config)
        except ValidationError as error:
            msg = invalid_settings_message(file_path, error)
        # Raise outside the handler so exception contexts cannot expose input values.
        raise ConfigError(msg)

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

        Raises
        ------
        ConfigError
            If the file is not valid YAML, is empty or is not a mapping
        """
        return read_environment_source(file_path)


def find_mlclient_environment(
    env_name: str,
) -> Path:
    """Return the configuration file path for a named MLClient environment.

    Searches the nearest .mlclient directory (see find_mlclient_directory) for a
    file matching the mlclient-<env_name>.yaml pattern.

    Parameters
    ----------
    env_name : str
        An MLClient environment name

    Returns
    -------
    Path
        The environment's configuration file path

    Raises
    ------
    MLClientDirectoryNotFoundError
        If no .mlclient directory has been found
    MLClientEnvironmentNotFoundError
        If the .mlclient directory has no mlclient-<env_name>.yaml file
    """
    ml_client_dir = find_mlclient_directory(Path.cwd())
    env_file_name = f"mlclient-{env_name}.yaml"
    env_file_path = next(ml_client_dir.glob(env_file_name), None)
    if not env_file_path:
        msg = (
            f"MLClient's environment configuration has not been found for [{env_name}]!"
        )
        raise MLClientEnvironmentNotFoundError(msg)
    logger.debug("MLClient configuration file found: [%s]", env_file_name)
    return env_file_path


def find_mlclient_directory(
    path: Path,
) -> Path:
    """Return the nearest .mlclient directory at path or in an ancestor.

    Searches path and its parents, excluding the filesystem root. When no
    .mlclient directory is found, checks home only if it was not already on
    the search path.

    Parameters
    ----------
    path : Path
        A path to start the search from

    Returns
    -------
    Path
        The located .mlclient directory

    Raises
    ------
    MLClientDirectoryNotFoundError
        If no .mlclient directory exists at path, any of its parents
        or the home directory
    """
    start_dir = path.absolute()
    directories = (start_dir, *start_dir.parents)
    for directory in directories:
        if directory.parent == directory:
            break
        mlclient_dir = directory / constants.ML_CLIENT_DIR
        if mlclient_dir.is_dir():
            logger.debug(
                "MLClient configuration home directory found: [%s]",
                mlclient_dir,
            )
            return mlclient_dir
    home_dir = Path.home()
    global_mlclient_dir = home_dir / constants.ML_CLIENT_DIR
    if home_dir not in directories and global_mlclient_dir.is_dir():
        logger.debug(
            "Using global configuration directory [%s]",
            global_mlclient_dir,
        )
        return global_mlclient_dir
    msg = (
        f"{constants.ML_CLIENT_DIR} directory has not been found in {start_dir} "
        f"or any of its parents (nor in {global_mlclient_dir}). "
        "Run 'ml env init' or 'ml env init --global'."
    )
    raise MLClientDirectoryNotFoundError(msg)


def no_such_app_server_error(
    environment: MLEnvironment,
    app_server_id: str,
    env_name: str | None = None,
) -> NoSuchAppServerError:
    """Build the error for an unknown app server, listing the configured ones.

    Each configured server is shown with its effective port, so predefined
    servers without an explicit port still show where they connect.

    Parameters
    ----------
    environment : MLEnvironment
        The environment that was searched.
    app_server_id : str
        The identifier that was not found.
    env_name : str | None, default None
        The environment's name; when given, the message names the environment.

    Returns
    -------
    NoSuchAppServerError
        The error to raise, listing the configured identifiers in
        configuration order.
    """
    scope = f" in the [{env_name}] environment" if env_name else ""
    available = ", ".join(
        f"{server_id} ({environment.provide_config_dict(server_id)['port']})"
        for server_id in environment.app_server_ids
    )
    msg = (
        f"There's no [{app_server_id}] app server configuration{scope}. "
        f"Available: {available}."
    )
    return NoSuchAppServerError(msg)


def read_environment_source(file_path: str, *, allow_empty: bool = False) -> dict:
    """Read a configuration mapping without resolving or validating its settings.

    Parameters
    ----------
    file_path : str
        Source YAML path.
    allow_empty : bool, default False
        Whether an empty document becomes an empty mapping for inspection.

    Returns
    -------
    dict
        Raw settings in their source order, without injected defaults.

    Raises
    ------
    ConfigError
        If YAML is invalid, the document is not a mapping, or it is empty and
        allow_empty is false. Messages omit configuration values and parser details.
    """
    source_config = _load_yaml(file_path)
    if source_config is None:
        if allow_empty:
            return {}
        msg = f"Environment configuration file is empty: {file_path}"
        raise ConfigError(msg)
    if not isinstance(source_config, dict):
        msg = f"Environment configuration must be a mapping: {file_path}"
        raise ConfigError(msg)
    return source_config


def invalid_settings_message(
    file_path: str,
    error: ValidationError,
) -> str:
    """Describe an environment's validation problems, one per line.

    Parameters
    ----------
    file_path : str
        The configuration file the settings come from.
    error : ValidationError
        The error raised by validating the settings.

    Returns
    -------
    str
        A header naming the file, then one line per problem with the field's
        location and the reason. Input values are left out, so a secret never
        appears in the message.
    """
    problems = [
        f"  {'.'.join(str(part) for part in issue['loc'])}: {_problem_reason(issue)}"
        for issue in error.errors(include_url=False, include_input=False)
    ]
    return "\n".join(
        [f"Invalid environment configuration in {file_path}:", *problems],
    )


def _problem_reason(
    issue: ErrorDetails,
) -> str:
    """Return a validation issue's reason in configuration-file terms."""
    if issue["type"] == "extra_forbidden":
        return "unknown setting"
    return issue["msg"].removeprefix("Value error, ")


def _load_yaml(
    file_path: str,
) -> object:
    """Parse a YAML file without exposing the parser's message.

    Parameters
    ----------
    file_path : str
        A source configuration's filepath

    Returns
    -------
    object
        The parsed document, or None for an empty file

    Raises
    ------
    ConfigError
        If the file is not valid YAML. The message names only the file.
    """
    with Path(file_path).open() as config_file:
        try:
            return yaml.safe_load(config_file)
        except yaml.YAMLError:
            msg = f"Invalid YAML in environment configuration file: {file_path}"
    # Parser messages can quote secrets. Raise outside the handler to discard
    # the parser exception context, including at verbose traceback levels.
    raise ConfigError(msg)


__all__ = [
    "DEFAULT_APP_SERVER_SETTINGS",
    "MLEnvironment",
    "MLServerConfig",
    "find_mlclient_directory",
    "find_mlclient_environment",
]
