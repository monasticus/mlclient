"""The ML Client Exceptions module.

It contains all custom exceptions related to ML Client:
    * WrongParametersError
        A custom Exception class for wrong parameters.
    * UnsupportedFormatError
        A custom Exception class for an unsupported format.
    * NoSuchAppServerError
        A custom Exception class for a non-existing app server configuration.
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


class NoSuchAppServerError(Exception):
    """A custom Exception class for a non-existing app server configuration.

    Raised when getting an app server config from an MLConfiguration instance.
    """
