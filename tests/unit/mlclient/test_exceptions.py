from __future__ import annotations

import pytest

from mlclient.exceptions import (
    ConfigError,
    EnvironmentFileExistsError,
    InvalidLogTypeError,
    InvalidMetadataError,
    MarkLogicError,
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
    MLClientError,
    NoRestServerConfiguredError,
    NoSuchAppServerError,
    NotARestServerError,
    ResourceNotFoundError,
    UnsupportedFileExtensionError,
    UnsupportedFormatError,
    WrongParametersError,
)


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


def test_marklogic_error_exposes_the_error_fields():
    error = MarkLogicError(
        {
            "errorResponse": {
                "statusCode": 404,
                "status": "Not Found",
                "messageCode": "RESTAPI-NODOCUMENT",
                "message": "RESTAPI-NODOCUMENT: Resource or document does not exist",
            },
        },
    )

    assert error.status_code == 404
    assert error.status == "Not Found"
    assert error.message_code == "RESTAPI-NODOCUMENT"
    assert error.message == "RESTAPI-NODOCUMENT: Resource or document does not exist"


def test_marklogic_error_leaves_missing_fields_empty():
    error = MarkLogicError({"statusCode": 404, "message": "No such resource"})

    assert error.status_code == 404
    assert error.status is None
    assert error.message_code is None
    assert error.message == "No such resource"


def test_marklogic_error_from_a_raw_message_has_no_fields():
    error = MarkLogicError("XDMP-BADCHAR: Unexpected character")

    assert error.status_code is None
    assert error.status is None
    assert error.message_code is None
    assert error.message is None


@pytest.mark.parametrize(
    "error",
    [
        ConfigError("invalid"),
        EnvironmentFileExistsError("/tmp/local.yaml"),
        InvalidLogTypeError("invalid"),
        InvalidMetadataError("invalid"),
        MLClientDirectoryNotFoundError("missing"),
        MLClientEnvironmentNotFoundError("missing"),
        MarkLogicError("XDMP-BADCHAR: Unexpected character"),
        NoRestServerConfiguredError("missing"),
        NoSuchAppServerError("missing"),
        NotARestServerError("invalid"),
        ResourceNotFoundError("missing"),
        UnsupportedFileExtensionError("invalid"),
        UnsupportedFormatError("invalid"),
        WrongParametersError("invalid"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_every_library_exception_is_an_mlclient_error(error):
    with pytest.raises(MLClientError):
        raise error


def test_marklogic_error_converts_a_management_api_status_code():
    error = MarkLogicError(
        {
            "errorResponse": {
                "statusCode": "400",
                "status": "Bad Request",
                "messageCode": "REST-INVALIDTYPE",
                "message": "REST-INVALIDTYPE: (rest:INVALIDTYPE) Invalid type in view",
            },
        },
    )

    assert error.status_code == 400
    assert str(error) == (
        "[400 Bad Request] (REST-INVALIDTYPE) "
        "REST-INVALIDTYPE: (rest:INVALIDTYPE) Invalid type in view"
    )
