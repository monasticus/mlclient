from __future__ import annotations

import json

from mlclient import constants, exceptions


def get_accept_header_for_format(
        data_format: str
):
    if data_format in ["xml"]:
        return constants.HEADER_XML
    elif data_format in ["json"]:
        return constants.HEADER_JSON
    elif data_format in ["html"]:
        return constants.HEADER_HTML
    elif data_format in ["text"]:
        return constants.HEADER_PLAIN_TEXT
    else:
        msg = f"Provided format [{data_format}] is not supported."
        raise exceptions.UnsupportedFormatError(msg)


def get_content_type_header_for_data(
        data
):
    try:
        if isinstance(data, dict):
            return constants.HEADER_JSON
        else:
            json.loads(data)
            return constants.HEADER_JSON
    except ValueError:
        return constants.HEADER_XML
