"""The ML Client Utils module.

It contains all useful functions shared in ML Client package and independent of
all classes. It exports following functions:

    * get_accept_header_for_format(data_format: str) -> str
        Return an Accept header for data format.
    * get_content_type_header_for_data(data: str | dict) -> str
        Return a Content-Type header for data provided.
"""
from __future__ import annotations

import json

from mlclient import constants, exceptions


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
    if data_format in ["xml"]:
        return constants.HEADER_XML
    if data_format in ["json"]:
        return constants.HEADER_JSON
    if data_format in ["html"]:
        return constants.HEADER_HTML
    if data_format in ["text"]:
        return constants.HEADER_PLAIN_TEXT

    msg = f"Provided format [{data_format}] is not supported."
    raise exceptions.UnsupportedFormatError(msg)


def get_content_type_header_for_data(
        data: str | dict,
) -> str:
    """Return a Content-Type header for data provided.

    Parameters
    ----------
    data : str | dict
        Data to send in a request

    Returns
    -------
    str
        A Content-Type header value
    """
    if isinstance(data, dict):
        return constants.HEADER_JSON
    try:
        json.loads(data)
    except ValueError:
        return constants.HEADER_XML
    else:
        return constants.HEADER_JSON
