"""The ML Client Constants module."""

from __future__ import annotations

# REQUEST METHODS
METHOD_GET = "GET"
METHOD_POST = "POST"
METHOD_PUT = "PUT"
METHOD_DELETE = "DELETE"

# HEADERS
HEADER_NAME_ACCEPT = "Accept"
HEADER_NAME_CONTENT_TYPE = "Content-Type"

HEADER_MULTIPART_MIXED = "multipart/mixed"
HEADER_XML = "application/xml"
HEADER_JSON = "application/json"
HEADER_X_WWW_FORM_URLENCODED = "application/x-www-form-urlencoded"
HEADER_HTML = "text/html"
HEADER_PLAIN_TEXT = "text/plain"

__all__ = ["METHOD_GET", "METHOD_POST", "METHOD_PUT", "METHOD_DELETE",
           "HEADER_NAME_ACCEPT", "HEADER_NAME_CONTENT_TYPE",
           "HEADER_MULTIPART_MIXED", "HEADER_XML", "HEADER_JSON",
           "HEADER_X_WWW_FORM_URLENCODED", "HEADER_HTML", "HEADER_PLAIN_TEXT"]
