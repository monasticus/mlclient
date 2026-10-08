"""The ML Client Utils module.

It contains all useful functions and classes shared in ML Client package.
It exports following functions:

    * get_accept_header_for_format(data_format: str) -> str
        Return an Accept header for data format.
    * get_content_type_header_for_data(data: str | dict) -> str
        Return a Content-Type header for data provided.
    * validate_supported(value, supported, plural_noun, *, required=False)
        Reject enumerated values outside a supported set.
    * query_params(params: dict, transform_params: dict | None) -> dict
        Return URL parameters without omitted values, plus transform parameters.
    * request_body_with_content_type(body, endpoint) -> tuple[str | dict, str]
        Validate a request body and return it with its Content-Type header value.
    * get_resource(resource_name: str) -> TextIO
        Return an MLClient resource.

It also exports a single class:

    * _BiDict
        A bidirectional dictionary.
"""

from __future__ import annotations

import importlib.resources as pkg_resources
import json
from collections.abc import Sequence
from typing import Any, TextIO

from mlclient import _constants as constants
from mlclient import exceptions
from mlclient import resources as data
from mlclient.exceptions import ResourceNotFoundError


def get_accept_header_for_format(
    data_format: str,
) -> str:
    """Return an Accept header for data format.

    Parameters
    ----------
    data_format : str
        Data format

    Returns
    -------
    str
        An Accept header value

    Raises
    ------
    UnsupportedFormatError
        If the format provided is not being supported
    """
    data_format = data_format.lower()

    if data_format == "xml":
        return constants.HEADER_XML
    if data_format == "json":
        return constants.HEADER_JSON
    if data_format == "html":
        return constants.HEADER_HTML
    if data_format == "text":
        return constants.HEADER_PLAIN_TEXT

    msg = f"Provided format [{data_format}] is not supported."
    raise exceptions.UnsupportedFormatError(msg)


def get_content_type_header_for_data(
    content: str | dict,
) -> str:
    """Return a Content-Type header for data provided.

    Parameters
    ----------
    content : str | dict
        Data to send in a request

    Returns
    -------
    str
        A Content-Type header value
    """
    if isinstance(content, dict):
        return constants.HEADER_JSON
    try:
        json.loads(content)
    except ValueError:
        return constants.HEADER_XML
    else:
        return constants.HEADER_JSON


def validate_supported(
    value: str | list | tuple | None,
    supported: Sequence[str],
    plural_noun: str,
    *,
    required: bool = False,
):
    """Reject enumerated parameter values MarkLogic does not accept.

    Parameters
    ----------
    value : str | list | tuple | None
        One value or several; None means the parameter is omitted.
    supported : Sequence[str]
        Accepted, case-sensitive values.
    plural_noun : str
        The parameter's plural name used in the error message, e.g. ``views``.
    required : bool, default False
        Whether an omitted value is rejected too.

    Raises
    ------
    WrongParametersError
        If a value, including an empty string, is outside the supported set,
        or the value is omitted although required.
    """
    values = value if isinstance(value, (list, tuple)) else [value]
    for item in values:
        omitted = item is None
        if (omitted and required) or (not omitted and item not in supported):
            msg = f"The supported {plural_noun} are: {', '.join(supported)}"
            raise exceptions.WrongParametersError(msg)


def query_params(params: dict, transform_params: dict | None) -> dict:
    """Return URL parameters, omitting None and prefixing transform parameters.

    Parameters
    ----------
    params : dict
        Parameter names mapped to values; only None is omitted, so zero and
        empty strings are sent. A tuple is sent as a list of repeated values.
    transform_params : dict | None
        Transform parameter names and values, sent with the ``trans:`` prefix.

    Returns
    -------
    dict
        Parameters to send.
    """
    transform_params = transform_params or {}
    return {
        **{
            name: list(value) if isinstance(value, tuple) else value
            for name, value in params.items()
            if value is not None
        },
        **{
            f"trans:{name}": value
            for name, value in transform_params.items()
            if value is not None
        },
    }


def request_body_with_content_type(
    body: str | dict | None,
    endpoint: str,
) -> tuple[str | dict, str]:
    """Validate a POST body and return it with its Content-Type header value.

    Parameters
    ----------
    body : str | dict | None
        A JSON dictionary, a JSON object string or an XML string.
    endpoint : str
        The endpoint named in error messages, e.g. ``POST /v1/search``.

    Returns
    -------
    tuple[str | dict, str]
        A JSON string is decoded to a dictionary; other bodies are unchanged.

    Raises
    ------
    WrongParametersError
        If the body is missing or blank, or is JSON but not a JSON object.
    """
    if body is None or (isinstance(body, str) and not body.strip()):
        msg = f"No request body provided for {endpoint}!"
        raise exceptions.WrongParametersError(msg)
    content_type = get_content_type_header_for_data(body)
    if content_type == constants.HEADER_JSON and isinstance(body, str):
        body = json.loads(body)
    if content_type == constants.HEADER_JSON and not isinstance(body, dict):
        msg = f"{endpoint} requires a JSON object or XML body"
        raise exceptions.WrongParametersError(msg)
    return body, content_type


def get_resource(
    resource_name: str,
) -> TextIO:
    """Return an MLClient resource.

    The resource needs to be included in mlclient.resources package
    to be returned.

    Parameters
    ----------
    resource_name : str
        An MLClient resource name

    Returns
    -------
    TextIO
        A MLClient resource

    Raises
    ------
    ResourceNotFoundError
        If the resource does not exist
    """
    try:
        return pkg_resources.open_text(data, resource_name)
    except FileNotFoundError:
        raise ResourceNotFoundError(resource_name) from FileNotFoundError


class _BiDict:
    """A bidirectional dictionary.

    This dict allows you to find a corresponding value by key in two directions.
    """

    def __init__(
        self,
        input_dict: dict,
    ):
        """Initialize a _BiDict instance.

        Parameters
        ----------
        input_dict : dict
            An input regular dictionary
        """
        self._origin = dict(input_dict)
        self._inverse = {value: key for key, value in input_dict.items()}

    def get(
        self,
        key: Any,
        default: Any = None,
    ) -> Any:
        """Return a corresponding value for a key regardless direction.

        Parameters
        ----------
        key : Any
            A dictionary key or value
        default : Ant, default None
            A default value

        Returns
        -------
        Any
            A corresponding value from the dictionary
        """
        return self._origin.get(key, self._inverse.get(key, default))
