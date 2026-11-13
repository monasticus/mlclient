from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.models import JSONDocument, TextDocument, XMLDocument
from tests.utils import resources as resources_utils

XQUERY_SOURCE_NAME = "mlclient-resources-test"


@pytest.fixture(scope="class")
def ml_client():
    with MLClient() as ml:
        yield ml


@pytest.fixture(scope="class")
def installed_extensions(ml_client: MLClient):
    xquery_extension = TestResourcesService.XQUERY_EXTENSION
    xquery_source = resources_utils.read_test_resource_text(__file__, "echo.xqy")
    javascript_source = resources_utils.read_test_resource_text(__file__, "echo.sjs")
    _install(
        ml_client,
        xquery_extension,
        xquery_source.replace(XQUERY_SOURCE_NAME, xquery_extension),
        "application/xquery",
    )
    try:
        _install(
            ml_client,
            TestResourcesService.JAVASCRIPT_EXTENSION,
            javascript_source,
            "application/vnd.marklogic-javascript",
        )
        yield
    finally:
        for name in (
            TestResourcesService.XQUERY_EXTENSION,
            TestResourcesService.JAVASCRIPT_EXTENSION,
        ):
            ml_client.http.delete(f"/v1/config/resources/{name}")


def _install(ml: MLClient, name: str, source: str, content_type: str):
    ml.http.put(
        f"/v1/config/resources/{name}",
        source,
        headers={"Content-Type": content_type},
    ).raise_for_status()


@pytest.mark.usefixtures("installed_extensions")
class TestResourcesService:
    XQUERY_EXTENSION = f"{XQUERY_SOURCE_NAME}-{uuid4().hex}"
    JAVASCRIPT_EXTENSION = f"{XQUERY_SOURCE_NAME}-sjs-{uuid4().hex}"
    MISSING_EXTENSION = f"{XQUERY_SOURCE_NAME}-missing-{uuid4().hex}"

    @pytest.mark.ml_access
    def test_get_receives_a_single_param(self, ml_client: MLClient):
        result = ml_client.resources.get(self.XQUERY_EXTENSION, {"a": "x"})

        assert result["method"] == "get"
        assert result["params"] == {"a": "x"}

    @pytest.mark.ml_access
    def test_get_receives_repeated_and_serialized_params(self, ml_client: MLClient):
        result = ml_client.resources.get(
            self.XQUERY_EXTENSION,
            {"a": ["x", "y"], "rs:flag": True, "n": 3},
        )

        assert result["params"] == {"a": ["x", "y"], "flag": "true", "n": "3"}

    @pytest.mark.ml_access
    def test_javascript_extension_receives_params(self, ml_client: MLClient):
        result = ml_client.resources.get(
            self.JAVASCRIPT_EXTENSION,
            {"a": ["x", "y"], "b": 1},
        )

        assert result == {"method": "get", "params": {"a": ["x", "y"], "b": "1"}}

    @pytest.mark.ml_access
    def test_post_sends_a_json_body(self, ml_client: MLClient):
        result = ml_client.resources.post(self.XQUERY_EXTENSION, {"k": 1}, {"a": "x"})

        assert result["method"] == "post"
        assert result["params"] == {"a": "x"}
        assert result["input-types"] == ["application/json"]

    @pytest.mark.ml_access
    def test_post_sends_documents_as_multipart(self, ml_client: MLClient):
        result = ml_client.resources.post(
            self.XQUERY_EXTENSION,
            [JSONDocument({"k": 1}), XMLDocument("<a/>"), TextDocument("hi")],
        )

        assert result["input-count"] == 3
        assert result["input-types"] == [
            "application/json",
            "application/xml",
            "text/plain",
        ]

    @pytest.mark.ml_access
    def test_post_returns_several_documents_as_a_list(self, ml_client: MLClient):
        result = ml_client.resources.post(
            self.XQUERY_EXTENSION,
            [JSONDocument({"k": 1}), TextDocument("hi")],
            {"echo": True},
        )

        assert result == [{"k": 1}, "hi"]

    @pytest.mark.ml_access
    def test_put_sends_a_str_body(self, ml_client: MLClient):
        result = ml_client.resources.put(
            self.XQUERY_EXTENSION,
            "<a/>",
            content_type="application/xml",
        )

        assert result["method"] == "put"
        assert result["input-types"] == ["application/xml"]

    @pytest.mark.ml_access
    def test_delete_receives_params(self, ml_client: MLClient):
        result = ml_client.resources.delete(self.XQUERY_EXTENSION, {"uri": "/a.json"})

        assert result["method"] == "delete"
        assert result["params"] == {"uri": "/a.json"}

    @pytest.mark.ml_access
    def test_scoped_service_runs_against_scope_database(self, ml_client: MLClient):
        modules = ml_client.eval.xquery("xdmp:database-name(xdmp:modules-database())")

        result = ml_client.resources(database=modules).get(self.XQUERY_EXTENSION)

        assert result["database"] == modules

    @pytest.mark.ml_access
    def test_missing_extension_raises_marklogic_error(self, ml_client: MLClient):
        with pytest.raises(MarkLogicError) as err:
            ml_client.resources.get(self.MISSING_EXTENSION)

        expected_msg = (
            "[500 Internal Server Error] (INTERNAL ERROR) RESTAPI-INVALIDREQ: "
            "(err:FOER0000) Invalid request:  reason: "
            f"Extension {self.MISSING_EXTENSION} or a dependency does not exist: "
            "XDMP-MODNOTFOUND: (err:XQST0059) Module "
            f"/marklogic.rest.resource/{self.MISSING_EXTENSION}/assets/resource.xqy "
            "not found . See the MarkLogic server error log for further detail."
        )
        assert str(err.value) == expected_msg

    @pytest.mark.ml_access
    def test_raw_get_rejects_an_unprefixed_param(self, ml_client: MLClient):
        resp = ml_client.http.get(
            f"/v1/resources/{self.XQUERY_EXTENSION}",
            params={"a": "x"},
        )
        prefixed_resp = ml_client.rest.resources.get(
            self.XQUERY_EXTENSION,
            params={"a": "x"},
        )

        assert resp.status_code == httpx.codes.BAD_REQUEST
        assert resp.json()["errorResponse"]["messageCode"] == "REST-UNSUPPORTEDPARAM"
        assert prefixed_resp.status_code == httpx.codes.OK
