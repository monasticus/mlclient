from pathlib import Path

import httpx
import pytest
import respx

from mlclient import MLClient
from mlclient.models.http import DocumentsBodyPart as BodyPart
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


@pytest.fixture
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element as element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@respx.mock
def test_eval(xquery):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": "xquery version '1.0-ml';"
            " declare variable $element as element() external;"
            " <new-parent>{$element/child::element()}</new-parent>",
            "vars": '{"element": "<parent><child/></parent>"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element()", "<new-parent><child/></new-parent>")
    ml_mocker.mock_post()

    with MLClient() as ml:
        resp = ml.rest.eval.post(
            xquery=xquery,
            variables={"element": "<parent><child/></parent>"},
        )

    assert resp.status_code == httpx.codes.OK
    assert "<new-parent><child/></new-parent>" in resp.text


@respx.mock
def test_get_documents():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-documents.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_request_param("uri", "/path/to/non-existing/document.xml")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    with MLClient() as ml:
        resp = ml.rest.documents.get(
            uri="/path/to/non-existing/document.xml",
            data_format="json",
        )

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert resp.json()["errorResponse"]["messageCode"] == "RESTAPI-NODOCUMENT"


@respx.mock
def test_post_documents():
    body_part = {
        "content-type": "application/json",
        "content-disposition": "inline",
        "content": {"root": "data"},
    }

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-documents.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    with MLClient() as ml:
        resp = ml.rest.documents.post([BodyPart(**body_part)])

    assert resp.status_code == httpx.codes.INTERNAL_SERVER_ERROR
    assert resp.json() == {
        "errorResponse": {
            "statusCode": "500",
            "status": "Internal Server Error",
            "messageCode": "XDMP-AS",
            "message": "XDMP-AS: (err:XPTY0004) $uri as xs:string -- "
            "Invalid coercion: () as xs:string",
        },
    }


@respx.mock
def test_delete_documents():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-delete-documents.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_request_param("uri", "/path/to/non-existing/document.xml")
    ml_mocker.with_request_param("result", "wiped")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_delete()

    with MLClient() as ml:
        resp = ml.rest.documents.delete(
            uri="/path/to/non-existing/document.xml",
            wipe_temporal=True,
        )

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert (
        "Endpoint does not support query parameter: "
        "invalid parameters: result "
        "for /path/to/non-existing/document.xml"
    ) in resp.text
