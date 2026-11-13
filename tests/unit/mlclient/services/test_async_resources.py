from __future__ import annotations

import httpx
import pytest
import pytest_asyncio
import respx

from mlclient import AsyncMLClient
from mlclient.exceptions import MarkLogicError, WrongParametersError
from mlclient.models import (
    BinaryDocument,
    JSONDocument,
    MetadataDocument,
    TextDocument,
    XMLDocument,
)
from mlclient.multipart import decode_multipart_mixed
from tests.utils.ml_mockers import MLRespXMocker

NAME = "mlclient-echo"
URL = f"http://localhost:8000/v1/resources/{NAME}"
JSON_CONTENT_TYPE = "application/json; charset=UTF-8"
NOT_INSTALLED_ERROR = (
    b'{"errorResponse":{"statusCode":500, "status":"Internal Server Error", '
    b'"messageCode":"INTERNAL ERROR", "message":"RESTAPI-INVALIDREQ: '
    b"(err:FOER0000) Invalid request:  reason: Extension mlclient-echo or a "
    b"dependency does not exist: XDMP-MODNOTFOUND: (err:XQST0059) Module "
    b"/marklogic.rest.resource/mlclient-echo/assets/resource.xqy not found . "
    b'See the MarkLogic server error log for further detail."}}'
)


class CustomMetadataDocument(MetadataDocument):
    """An application's metadata-only document subclass."""


@pytest_asyncio.fixture
async def ml() -> AsyncMLClient:
    async with AsyncMLClient() as client:
        yield client


def _mock_json_response(method: str, body: bytes, **request) -> respx.Route:
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(URL)
    for name, value in request.get("params", []):
        ml_mocker.with_request_param(name, value)
    if "content_type" in request:
        ml_mocker.with_request_content_type(request["content_type"])
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    ml_mocker.with_response_body(body)
    return getattr(ml_mocker, f"mock_{method}")()


def _sent(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


# --- parameters ---


@pytest.mark.asyncio
@respx.mock
async def test_get_sends_params_with_the_rs_prefix(ml):
    _mock_json_response(
        "get",
        b'{"method":"get", "params":{"a":"x"}}',
        params=[("rs:a", "x")],
    )

    result = await ml.resources.get(NAME, {"a": "x"})

    assert result == {"method": "get", "params": {"a": "x"}}


@pytest.mark.asyncio
@respx.mock
async def test_get_keeps_params_already_prefixed(ml):
    route = _mock_json_response("get", b'{"method":"get", "params":{"a":"x"}}')

    await ml.resources.get(NAME, {"rs:a": "x"})

    assert _sent(route).url.params.multi_items() == [("rs:a", "x")]


@pytest.mark.asyncio
@respx.mock
async def test_get_repeats_list_params(ml):
    route = _mock_json_response(
        "get",
        b'{"method":"get", "params":{"a":["x", "y"]}}',
    )

    result = await ml.resources.get(NAME, {"a": ["x", "y"]})

    assert _sent(route).url.params.multi_items() == [("rs:a", "x"), ("rs:a", "y")]
    assert result == {"method": "get", "params": {"a": ["x", "y"]}}


@pytest.mark.asyncio
@respx.mock
async def test_get_serializes_booleans_and_numbers(ml):
    route = _mock_json_response(
        "get",
        b'{"method":"get", "params":{"n":"3", "flag":"true", "off":"false"}}',
    )

    await ml.resources.get(NAME, {"flag": True, "off": False, "n": 3})

    assert _sent(route).url.params.multi_items() == [
        ("rs:flag", "true"),
        ("rs:off", "false"),
        ("rs:n", "3"),
    ]


@pytest.mark.asyncio
@respx.mock
async def test_get_without_params(ml):
    route = _mock_json_response("get", b'{"method":"get", "params":{}}')

    result = await ml.resources.get(NAME)

    assert _sent(route).url.params.multi_items() == []
    assert result == {"method": "get", "params": {}}


@pytest.mark.asyncio
async def test_blank_name_is_rejected_before_any_request(ml):
    with pytest.raises(WrongParametersError) as err:
        await ml.resources.get(" ")

    assert str(err.value) == "No resource name provided for /v1/resources/{name}!"


# --- results ---


@pytest.mark.asyncio
@respx.mock
async def test_get_parses_an_xml_result(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", "application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        b'<?xml version="1.0" encoding="UTF-8"?>\n<report year="2026"/>',
    )
    ml_mocker.mock_get()

    result = await ml.resources.get(NAME)

    assert result.getroot().tag == "report"
    assert result.getroot().attrib == {"year": "2026"}


@pytest.mark.asyncio
@respx.mock
async def test_get_parses_a_multipart_result_into_a_list(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(None, '{"k":1}', "application/json")
    ml_mocker.with_response_body_part(None, "hi", "text/plain")
    ml_mocker.mock_get()

    result = await ml.resources.get(NAME)

    assert result == [{"k": 1}, "hi"]


@pytest.mark.asyncio
@respx.mock
async def test_delete_with_empty_result(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(URL)
    ml_mocker.with_request_param("rs:uri", "/a.json")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    result = await ml.resources.delete(NAME, {"uri": "/a.json"})

    assert result == []


# --- bodies ---


@pytest.mark.asyncio
@respx.mock
async def test_post_without_body(ml):
    route = _mock_json_response("post", b'{"method":"post", "input-count":1}')

    result = await ml.resources.post(NAME)

    assert _sent(route).content == b""
    assert "content-type" not in _sent(route).headers
    assert result == {"method": "post", "input-count": 1}


@pytest.mark.asyncio
@respx.mock
async def test_post_sends_a_dict_as_json(ml):
    route = _mock_json_response(
        "post",
        b'{"method":"post", "input-types":["application/json"]}',
        params=[("rs:a", "x")],
        content_type="application/json",
    )

    result = await ml.resources.post(NAME, {"k": 1}, {"a": "x"})

    assert _sent(route).content == b'{"k": 1}'
    assert result == {"method": "post", "input-types": ["application/json"]}


@pytest.mark.asyncio
@respx.mock
async def test_post_sends_a_list_as_json(ml):
    route = _mock_json_response(
        "post",
        b'{"method":"post", "input-types":["application/json"]}',
        content_type="application/json",
    )

    await ml.resources.post(NAME, [1, {"k": 2}])

    assert _sent(route).content == b'[1, {"k": 2}]'


@pytest.mark.asyncio
@respx.mock
async def test_post_sends_an_empty_list_as_json(ml):
    route = _mock_json_response(
        "post",
        b'{"method":"post", "input-types":["application/json"]}',
        content_type="application/json",
    )

    await ml.resources.post(NAME, [])

    assert _sent(route).content == b"[]"


@pytest.mark.asyncio
@respx.mock
async def test_post_sends_a_str_with_its_content_type(ml):
    route = _mock_json_response(
        "post",
        b'{"method":"post", "input-types":["application/xml"]}',
        content_type="application/xml",
    )

    await ml.resources.post(NAME, "<a/>", content_type="application/xml")

    assert _sent(route).content == b"<a/>"


@pytest.mark.asyncio
@respx.mock
async def test_post_sends_bytes_with_their_content_type(ml):
    route = _mock_json_response(
        "post",
        b'{"method":"post", "input-types":["application/octet-stream"]}',
        content_type="application/octet-stream",
    )

    await ml.resources.post(NAME, b"\x00\x01", content_type="application/octet-stream")

    assert _sent(route).content == b"\x00\x01"


@pytest.mark.asyncio
@pytest.mark.parametrize("body", ["<a/>", b"\x00\x01"])
async def test_post_str_or_bytes_without_content_type_is_rejected(ml, body):
    with pytest.raises(WrongParametersError) as err:
        await ml.resources.post(NAME, body)

    assert str(err.value) == "A str or bytes body requires a content_type!"


@pytest.mark.asyncio
async def test_post_unsupported_body_is_rejected(ml):
    with pytest.raises(WrongParametersError) as err:
        await ml.resources.post(NAME, 42)

    assert str(err.value) == "The body must be a dict, list, str or bytes, got int"


@pytest.mark.parametrize(
    ("document", "content_type", "content"),
    [
        (JSONDocument({"k": 1}, "/a.json"), "application/json", b'{"k": 1}'),
        (XMLDocument("<a/>", "/a.xml"), "application/xml", b"<a/>"),
        (TextDocument("hi", "/a.txt"), "text/plain", b"hi"),
        (BinaryDocument(b"\x00", "/a.png"), "image/png", b"\x00"),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_post_sends_a_document_with_the_content_type_of_its_uri(
    ml,
    document,
    content_type,
    content,
):
    route = _mock_json_response(
        "post",
        b'{"method":"post", "input-count":1}',
        content_type=content_type,
    )

    await ml.resources.post(NAME, document)

    assert _sent(route).content == content


@pytest.mark.parametrize(
    ("document", "content_type"),
    [
        (JSONDocument({"k": 1}), "application/json"),
        (XMLDocument("<a/>"), "application/xml"),
        (TextDocument("hi", "/a.unknown-extension"), "text/plain"),
        (BinaryDocument(b"\x00"), "application/octet-stream"),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_post_sends_a_document_without_a_known_uri_by_document_type(
    ml,
    document,
    content_type,
):
    _mock_json_response(
        "post",
        b'{"method":"post", "input-count":1}',
        content_type=content_type,
    )

    assert await ml.resources.post(NAME, document) == {
        "method": "post",
        "input-count": 1,
    }


@pytest.mark.asyncio
@respx.mock
async def test_post_sends_documents_as_multipart(ml):
    route = _mock_json_response(
        "post",
        b'{"method":"post", "input-count":2, '
        b'"input-types":["application/json", "application/xml"]}',
    )

    await ml.resources.post(
        NAME,
        [JSONDocument({"k": 1}, "/a.json"), XMLDocument("<a/>")],
    )

    request = _sent(route)
    parts = decode_multipart_mixed(request.content, request.headers["Content-Type"])
    assert request.headers["Content-Type"].startswith("multipart/mixed; boundary=")
    assert [(part.headers, part.content) for part in parts] == [
        ({"Content-Type": "application/json"}, b'{"k": 1}'),
        ({"Content-Type": "application/xml"}, b"<a/>"),
    ]


@pytest.mark.asyncio
async def test_post_document_with_content_type_is_rejected(ml):
    with pytest.raises(WrongParametersError) as err:
        await ml.resources.post(NAME, TextDocument("hi"), content_type="text/plain")

    expected = "A Document body carries its own content type; omit content_type!"
    assert str(err.value) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("metadata_type", [MetadataDocument, CustomMetadataDocument])
async def test_post_metadata_document_is_rejected(ml, metadata_type):
    with pytest.raises(WrongParametersError) as err:
        await ml.resources.post(NAME, [metadata_type("/a.json", '{"quality": 1}')])

    expected = "A MetadataDocument has no content to send to a resource extension!"
    assert str(err.value) == expected


@pytest.mark.asyncio
@respx.mock
async def test_put_sends_a_dict_as_json(ml):
    route = _mock_json_response(
        "put",
        b'{"method":"put", "input-types":["application/json"]}',
        params=[("rs:a", "x")],
        content_type="application/json",
    )

    result = await ml.resources.put(NAME, {"k": 1}, {"a": "x"})

    assert _sent(route).content == b'{"k": 1}'
    assert result == {"method": "put", "input-types": ["application/json"]}


@pytest.mark.asyncio
@respx.mock
async def test_put_sends_documents_as_multipart(ml):
    route = _mock_json_response("put", b'{"method":"put", "input-count":2}')

    await ml.resources.put(NAME, [TextDocument("a"), TextDocument("b")])

    request = _sent(route)
    parts = decode_multipart_mixed(request.content, request.headers["Content-Type"])
    assert [part.content for part in parts] == [b"a", b"b"]


# --- scope ---


@pytest.mark.asyncio
@respx.mock
async def test_operation_database_and_txid(ml):
    route = _mock_json_response("get", b'{"method":"get", "params":{}}')

    await ml.resources.get(NAME, database="Documents", txid="123")

    assert dict(_sent(route).url.params) == {"database": "Documents", "txid": "123"}


@pytest.mark.asyncio
@respx.mock
async def test_scoped_service_sends_its_database_and_txid(ml):
    route = _mock_json_response("delete", b'{"method":"delete", "params":{}}')

    await ml.resources(database="Documents", txid="123").delete(NAME)

    assert dict(_sent(route).url.params) == {"database": "Documents", "txid": "123"}


@pytest.mark.asyncio
@respx.mock
async def test_operation_overrides_and_clears_the_scope(ml):
    route = _mock_json_response("post", b'{"method":"post", "input-count":1}')

    await ml.resources(database="Documents", txid="123").post(
        NAME,
        database="Modules",
        txid=None,
    )

    assert dict(_sent(route).url.params) == {"database": "Modules"}


@pytest.mark.asyncio
async def test_scoped_copy_leaves_the_original_unchanged(ml):
    scoped = ml.resources(database="Documents")

    assert scoped is not ml.resources
    assert type(scoped) is type(ml.resources)


# --- errors ---


@pytest.mark.asyncio
@respx.mock
async def test_marklogic_error_is_raised(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(URL)
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    ml_mocker.with_response_body(NOT_INSTALLED_ERROR)
    ml_mocker.mock_get()

    with pytest.raises(MarkLogicError) as err:
        await ml.resources.get(NAME)

    expected_msg = (
        "[500 Internal Server Error] (INTERNAL ERROR) RESTAPI-INVALIDREQ: "
        "(err:FOER0000) Invalid request:  "
        "reason: Extension mlclient-echo or a dependency does not exist: "
        "XDMP-MODNOTFOUND: (err:XQST0059) Module "
        "/marklogic.rest.resource/mlclient-echo/assets/resource.xqy not found . "
        "See the MarkLogic server error log for further detail."
    )
    assert str(err.value) == expected_msg


@pytest.mark.asyncio
@respx.mock
async def test_http_error_without_marklogic_payload_is_raised(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(URL)
    ml_mocker.with_response_code(502)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()

    with pytest.raises(httpx.HTTPStatusError):
        await ml.resources.get(NAME)


@pytest.mark.asyncio
@respx.mock
async def test_post_accepts_a_document_subclass(ml):
    class ProductDocument(JSONDocument):
        """A domain document inheriting its JSON content implementation."""

    route = _mock_json_response("post", b'{"method":"post"}')

    result = await ml.resources.post(NAME, ProductDocument({"k": 1}))

    assert _sent(route).content == b'{"k": 1}'
    assert _sent(route).headers["Content-Type"] == "application/json"
    assert result == {"method": "post"}
