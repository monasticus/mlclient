from __future__ import annotations

from mlclient.exceptions import MarkLogicError


def test_marklogic_error_unwraps_the_error_response_envelope():
    error = {
        "errorResponse": {
            "statusCode": 500,
            "status": "Internal Server Error",
            "messageCode": "ADMIN-DUPLICATENAME",
            "message": "Trace Event already exists",
        },
    }

    assert str(MarkLogicError(error)) == (
        "[500 Internal Server Error] (ADMIN-DUPLICATENAME) Trace Event already exists"
    )


def test_marklogic_error_accepts_a_bare_error_object():
    error = {
        "statusCode": 404,
        "status": "Not Found",
        "message": "No such resource",
    }

    assert str(MarkLogicError(error)) == "[404 Not Found] No such resource"


def test_marklogic_error_uses_a_raw_message_verbatim():
    assert str(MarkLogicError("XDMP-BADCHAR: Unexpected character")) == (
        "XDMP-BADCHAR: Unexpected character"
    )
