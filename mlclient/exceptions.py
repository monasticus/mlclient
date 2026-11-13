"""The ML Client Exceptions module.

It contains all custom exceptions related to ML Client. Each of them subclasses
MLClientError, so ``except MLClientError`` catches every error mlclient raises
itself. Transport and HTTP status failures come from httpx unwrapped; their common
base is ``httpx.HTTPError``.

    * MLClientError
        The base class of every ML Client exception.
    * WrongParametersError
        A custom Exception class for wrong parameters.
    * UnsupportedFormatError
        A custom Exception class for an unsupported format.
    * MLClientDirectoryNotFoundError
        A custom Exception class for a non-existing MLClient configuration directory.
    * MLClientEnvironmentNotFoundError
        A custom Exception class for a non-existing MLClient environment.
    * NoSuchAppServerError
        A custom Exception class for a non-existing app server configuration.
    * NotARestServerError
        A custom Exception class for a regular App-Server used as a REST Server.
    * NoRestServerConfiguredError
        A custom Exception class for no REST Server configured when required.
    * InvalidLogTypeError
        A custom Exception class for an invalid log type.
    * MarkLogicError
        A custom Exception class representing MarkLogic errors.
    * UnsupportedFileExtensionError
        A custom Exception class for an unsupported file extension.
    * InvalidMetadataError
        A custom Exception class for invalid metadata XML.
    * ResourceNotFoundError
        A custom Exception class for a not found resource.
    * ConfigError
        A custom Exception class for invalid connection/authentication config.
    * EnvironmentFileExistsError
        A custom Exception class for an already existing environment file.
"""

from __future__ import annotations


class MLClientError(Exception):
    """The base class of every ML Client exception.

    Catch it to handle any error raised by mlclient itself; transport and
    HTTP status failures raised by httpx derive from ``httpx.HTTPError``.
    """


class WrongParametersError(MLClientError):
    """A custom Exception class for wrong parameters.

    Raised when attempting to call a REST Resource with incorrect parameters.
    """


class ConfigError(MLClientError):
    """A custom Exception class for invalid connection/authentication config.

    Raised at client creation time when connection and authentication settings
    form a combination MarkLogic cannot support (e.g. certificate auth without
    a client certificate, or a Cloud connection mixed with explicit auth).
    """


class UnsupportedFormatError(MLClientError):
    """A custom Exception class for an unsupported format.

    Raised when getting an Accept header for a format.
    """


class MLClientDirectoryNotFoundError(MLClientError):
    """A custom Exception class for a non-existing MLClient configuration directory.

    Raised when loading an MLEnvironment.
    """


class MLClientEnvironmentNotFoundError(MLClientError):
    """A custom Exception class for a non-existing MLClient environment.

    Raised when loading an MLEnvironment.
    """


class NoSuchAppServerError(MLClientError):
    """A custom Exception class for a non-existing app server configuration.

    Raised when getting an app server config from an MLEnvironment instance.
    """


class NotARestServerError(MLClientError):
    """A custom Exception class for a regular App-Server used as a REST Server.

    Raised while getting an app server config not being a REST server.
    """


class NoRestServerConfiguredError(MLClientError):
    """A custom Exception class for no REST Server configured when required.

    Raised while getting an app server config when no REST server is configured.
    """


class InvalidLogTypeError(MLClientError):
    """A custom Exception class for an invalid log type.

    Raised while getting LogType enum for a value different from error, access
    and request.
    """


class MarkLogicError(MLClientError):
    """A custom Exception class representing MarkLogic errors.

    Raised whenever an ML server returns an error.

    Attributes
    ----------
    status_code : int | None
        The HTTP status code MarkLogic reported, e.g. ``404``; the Management
        API reports it as a string, which is converted
    status : str | None
        The HTTP status text MarkLogic reported, e.g. ``"Not Found"``
    message_code : str | None
        The MarkLogic error code, e.g. ``"RESTAPI-NODOCUMENT"``
    message : str | None
        The MarkLogic error message

    All four are ``None`` when the error was created from a raw message.

    Examples
    --------
    >>> from mlclient.exceptions import MarkLogicError
    >>> error = MarkLogicError(
    ...     {
    ...         "errorResponse": {
    ...             "statusCode": 404,
    ...             "status": "Not Found",
    ...             "messageCode": "RESTAPI-NODOCUMENT",
    ...             "message": "RESTAPI-NODOCUMENT: No such document",
    ...         },
    ...     },
    ... )
    >>> error.message_code
    'RESTAPI-NODOCUMENT'
    """

    def __init__(
        self,
        error: dict | str,
    ):
        """Initialize MarkLogicError instance.

        Parameters
        ----------
        error : dict | str
            An error response object, with or without the ``errorResponse``
            envelope, or a raw error message
        """
        self.status_code: int | None = None
        self.status: str | None = None
        self.message_code: str | None = None
        self.message: str | None = None
        if isinstance(error, dict):
            error = error.get("errorResponse", error)
            status_code = error.get("statusCode")
            self.status_code = int(status_code) if str(status_code).isdigit() else None
            self.status = error.get("status")
            self.message_code = error.get("messageCode")
            self.message = error.get("message")
            if self.message_code:
                error_msg = (
                    f"[{status_code} {self.status}] "
                    f"({self.message_code}) {self.message}"
                )
            else:
                error_msg = f"[{status_code} {self.status}] {self.message}"
        else:
            error_msg = error
        super().__init__(error_msg)


class UnsupportedFileExtensionError(MLClientError):
    """A custom Exception class for an unsupported file extension.

    Raised while evaluating code from file with unsupported extension.
    """


class InvalidMetadataError(MLClientError):
    """A custom Exception class for invalid metadata XML.

    Raised when parsing a metadata XML file with unexpected elements or namespaces.
    """


class ResourceNotFoundError(MLClientError):
    """A custom Exception class for a not found resource.

    Raised while attempting to get a resource that does not exist.
    """

    def __init__(
        self,
        resource_name: str,
    ):
        """Initialize ResourceNotFoundError exception with details.

        Extends Exception constructor with a custom message.

        Parameters
        ----------
        resource_name : str
            A resource name
        """
        super().__init__(f"No such resource: [{resource_name}]")


class EnvironmentFileExistsError(MLClientError):
    """A custom Exception class for an already existing environment file.

    Raised when scaffolding an environment configuration that would overwrite
    an existing file without the force flag.
    """

    def __init__(
        self,
        file_path: str,
    ):
        """Initialize EnvironmentFileExistsError exception with details.

        Extends Exception constructor with a custom message.

        Parameters
        ----------
        file_path : str
            A path of the existing configuration file
        """
        super().__init__(
            f"Configuration file already exists: [{file_path}]. Use --force to "
            f"overwrite.",
        )


__all__ = [
    "ConfigError",
    "EnvironmentFileExistsError",
    "InvalidLogTypeError",
    "InvalidMetadataError",
    "MLClientDirectoryNotFoundError",
    "MLClientEnvironmentNotFoundError",
    "MLClientError",
    "MarkLogicError",
    "NoRestServerConfiguredError",
    "NoSuchAppServerError",
    "NotARestServerError",
    "ResourceNotFoundError",
    "UnsupportedFileExtensionError",
    "UnsupportedFormatError",
    "WrongParametersError",
]
