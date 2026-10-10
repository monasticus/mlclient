"""Shared request validation and encoding for Call implementations."""

from __future__ import annotations

import json
from collections.abc import Sequence

from mlclient import _constants as constants, _utils as utils, exceptions


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
    content_type = utils.get_content_type_header_for_data(body)
    if content_type == constants.HEADER_JSON and isinstance(body, str):
        body = json.loads(body)
    if content_type == constants.HEADER_JSON and not isinstance(body, dict):
        msg = f"{endpoint} requires a JSON object or XML body"
        raise exceptions.WrongParametersError(msg)
    return body, content_type


