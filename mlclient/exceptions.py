"""The ML Client Exceptions module.

It contains all custom exceptions related to ML Client:
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
    * MarkLogicError
        A custom Exception class representing MarkLogic errors.
    * UnsupportedFileExtensionError
        A custom Exception class for an unsupported file extension.
"""
from __future__ import annotations


class WrongParametersError(Exception):
    """A custom Exception class for wrong parameters.

    Raised when attempting to call a REST Resource with incorrect parameters.
    """


class UnsupportedFormatError(Exception):
    """A custom Exception class for an unsupported format.

    Raised when getting an Accept header for a format.
    """


class MLClientDirectoryNotFoundError(Exception):
    """A custom Exception class for a non-existing MLClient configuration directory.

    Raised when initializing an MLConfiguration from an environment.
    """


class MLClientEnvironmentNotFoundError(Exception):
    """A custom Exception class for a non-existing MLClient environment.

    Raised when initializing an MLConfiguration from an environment.
    """


class NoSuchAppServerError(Exception):
    """A custom Exception class for a non-existing app server configuration.

    Raised when getting an app server config from an MLConfiguration instance.
    """


class NotARestServerError(Exception):
    """A custom Exception class for a regular App-Server used as a REST Server.

    Raised while getting an app server config not being a REST server.
    """


class NoRestServerConfiguredError(Exception):
    """A custom Exception class for no REST Server configured when required.

    Raised while getting an app server config when no REST server is configured.
    """


class InvalidLogTypeError(Exception):
    """A custom Exception class for an invalid log type.

    Raised while getting LogType enum for a value different from error, access
    and request.
    """


class MarkLogicError(Exception):
    """A custom Exception class representing MarkLogic errors.

    Raised whenever an ML server returns an error.
    """

    def __init__(
            self,
            error: dict | str,
    ):
        """Initialize MarkLogicError instance.

        Parameters
        ----------
        error : dict | str
            An error response object or a raw error message
        """
        if isinstance(error, dict):
            status_code = error.get("statusCode")
            status = error.get("status")
            msg_code = error.get("messageCode")
            msg = error.get("message")
            if msg_code:
                error_msg = f"[{status_code} {status}] ({msg_code}) {msg}"
            else:
                error_msg = f"[{status_code} {status}] {msg}"
        else:
            error_msg = error
        super().__init__(error_msg)


class UnsupportedFileExtensionError(Exception):
    """A custom Exception class for an unsupported file extension.

    Raised while evaluating code from file with unsupported extension.
    """
