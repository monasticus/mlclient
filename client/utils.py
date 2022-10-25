from client import constants
from client import exceptions


def get_accept_header_for_format(data_format: str):
    if data_format in ["xml"]:
        return constants.HEADER_CONTENT_TYPE_XML
    elif data_format in ["json"]:
        return constants.HEADER_CONTENT_TYPE_JSON
    elif data_format in ["html"]:
        return constants.HEADER_CONTENT_TYPE_HTML
    elif data_format in ["text"]:
        return constants.HEADER_CONTENT_TYPE_PLAIN_TEXT
    else:
        raise exceptions.UnsupportedFormat(f"Provided format [{data_format}] is not supported.")
