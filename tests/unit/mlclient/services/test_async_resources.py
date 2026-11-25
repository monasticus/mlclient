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
    with (
        respx.mock(assert_all_called=False) as router,
        pytest.raises(WrongParametersError) as err,
    ):
        await ml.resources.get(" ")

    assert str(err.value) == "No resource name provided for /v1/resources/{name}!"
    assert router.calls.call_count == 0


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


@pytest.mark.asyncio
async def test_post_list_mixing_documents_and_json_values_is_rejected(ml):
    with pytest.raises(WrongParametersError) as err:
        await ml.resources.post(NAME, [JSONDocument({"k": 1}, "/a.json"), {"k": 2}])

    assert str(err.value) == "A list body must hold only Documents or only JSON values!"


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
async def test_post_accepts_a_document_subclass(ml):
    class ProductDocument(JSONDocument):
        """A domain document inheriting its JSON content implementation."""

    route = _mock_json_response("post", b'{"method":"post"}')

    result = await ml.resources.post(NAME, ProductDocument({"k": 1}))

    assert _sent(route).content == b'{"k": 1}'
    assert _sent(route).headers["Content-Type"] == "application/json"
    assert result == {"method": "post"}


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


# --- response format ---


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
async def test_format_is_sent_as_the_accept_header(ml, method):
    route = _mock_json_response(method, b'{"method":"%s"}' % method.encode())

    await getattr(ml.resources, method)(NAME, data_format="xml")

    assert _sent(route).headers["Accept"] == "application/xml"


@pytest.mark.asyncio
@respx.mock
async def test_get_parses_a_csv_result(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(URL)
    ml_mocker.with_request_header("Accept", "text/csv")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("Content-Type", "text/csv; charset=UTF-8")
    ml_mocker.with_response_body(b"a,b\n1,2")
    ml_mocker.mock_get()

    assert await ml.resources.get(NAME, data_format="csv") == "a,b\n1,2"


@pytest.mark.asyncio
@respx.mock
async def test_unsupported_format_is_rejected_before_any_request(ml):
    router = respx.route(url__startswith=URL)

    with pytest.raises(WrongParametersError) as err:
        await ml.resources.get(NAME, data_format="yaml")

    assert str(err.value) == "The supported formats are: json, xml, html, text, csv"
    assert router.calls.call_count == 0


# --- database and transaction scope ---


@pytest.mark.asyncio
@respx.mock
async def test_get_with_scope_kwargs(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url(URL)
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_response_code(200)
    mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    mocker.with_response_body(b'{"method":"get", "params":{}}')
    mocker.mock_get()

    result = await ml.resources.get(NAME, database="request-db", txid="request-tx")

    assert result == {"method": "get", "params": {}}


@pytest.mark.asyncio
@respx.mock
async def test_post_inherits_service_scope(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url(URL)
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_response_code(200)
    mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    mocker.with_response_body(b'{"method":"post", "input-count":1}')
    mocker.mock_post()

    result = await ml.resources(database="service-db", txid="service-tx").post(NAME)

    assert result == {"method": "post", "input-count": 1}


@pytest.mark.asyncio
@respx.mock
async def test_put_scope_kwargs_override_service_scope(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url(URL)
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/json")
    mocker.with_response_code(200)
    mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    mocker.with_response_body(b'{"method":"put", "input-count":1}')
    mocker.mock_put()

    result = await ml.resources(database="service-db", txid="service-tx").put(
        NAME,
        {"k": 1},
        database="request-db",
        txid="request-tx",
    )

    assert result == {"method": "put", "input-count": 1}


@pytest.mark.asyncio
@respx.mock
async def test_delete_scope_kwargs_clear_service_database(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url(URL)
    mocker.with_request_param("txid", "service-tx")
    mocker.with_response_code(200)
    mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    mocker.with_response_body(b'{"method":"delete", "params":{}}')
    mocker.mock_delete()

    result = await ml.resources(database="service-db", txid="service-tx").delete(
        NAME,
        database=None,
    )

    assert result == {"method": "delete", "params": {}}


@pytest.mark.asyncio
@respx.mock
async def test_get_scope_kwargs_clear_service_transaction(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url(URL)
    mocker.with_request_param("database", "service-db")
    mocker.with_response_code(200)
    mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    mocker.with_response_body(b'{"method":"get", "params":{}}')
    mocker.mock_get()

    result = await ml.resources(database="service-db", txid="service-tx").get(
        NAME,
        txid=None,
    )

    assert result == {"method": "get", "params": {}}


@pytest.mark.asyncio
@respx.mock
async def test_overriding_scope_on_service_copy_preserves_original_scope(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url(URL)
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-2")
    mocker.with_response_code(200)
    mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    mocker.with_response_body(b'{"method":"get", "params":{}}')
    mocker.mock_get()
    mocker.with_url(URL)
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.with_response_code(200)
    mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    mocker.with_response_body(b'{"method":"get", "params":{}}')
    mocker.mock_get()

    original_service = ml.resources(database="catalog", txid="tx-1")
    overridden_scope_service = original_service(txid="tx-2")
    await overridden_scope_service.get(NAME)
    await original_service.get(NAME)


# --- timeout ---


@pytest.mark.asyncio
@respx.mock
async def test_get_timeout_reaches_transport_and_is_not_an_extension_param(ml):
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url(URL)
    mocker.with_request_param("rs:timeout", "30")
    mocker.with_response_code(200)
    mocker.with_response_header("Content-Type", JSON_CONTENT_TYPE)
    mocker.with_response_body(b'{"method":"get", "params":{"timeout":"30"}}')
    route = mocker.mock_get()

    result = await ml.resources.get(NAME, {"timeout": 30}, timeout=2)

    assert result == {"method": "get", "params": {"timeout": "30"}}
    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


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
async def test_bodyless_http_failure_is_raised_with_its_response(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_get()

    with pytest.raises(httpx.HTTPStatusError) as raised:
        await ml.resources.get(NAME)

    assert route.call_count == 1
    assert raised.value.response.url == route.calls.last.request.url
    assert raised.value.response.status_code == 403


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
