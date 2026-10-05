"""Public MCP contracts; parsed-value mocks exercise serialization, not MarkLogic."""

from __future__ import annotations

import asyncio
import json
import sys
import xml.etree.ElementTree as ElemTree
from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest
import respx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp.exceptions import ToolError

from mlclient import AsyncMLClient, MLClientManager
from mlclient.api import AsyncDatabasesApi, AsyncHostsApi
from mlclient.clients import AsyncHttpClient
from mlclient.mcp import main, mcp
from mlclient.models import Document, Metadata
from mlclient.services import AsyncDocumentsService, AsyncEvalService
from mlclient.services.diagnostics import AsyncLogsService
from tests.utils import resources as resources_utils


@pytest.fixture(autouse=True)
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / ".mlclient"
    directory.mkdir()
    (directory / "mlclient-local.yaml").write_text(
        "app-name: mcp-test\nhost: localhost\nusername: admin\npassword: admin\n"
        "protocol: http\napp-servers:\n"
        "  - id: content\n    port: 8100\n    auth: digest\n    rest: true\n"
        "  - id: alternate\n    port: 8101\n    auth: digest\n    rest: true\n",
    )
    return directory


async def call(name, **params):
    content, result = await mcp.call_tool(name, {"params": params})
    assert json.loads(content[0].text) == result
    return result


@pytest.mark.asyncio
async def test_envs_discovers_names_in_project(project):
    (project / "mlclient-dev.yaml").write_text("host: dev")
    content, result = await mcp.call_tool("MLClientEnvs", {})
    assert json.loads(content[0].text) == result
    assert result == {
        "directory": str(project),
        "count": 2,
        "environments": [
            {"name": "dev", "file": str(project / "mlclient-dev.yaml")},
            {"name": "local", "file": str(project / "mlclient-local.yaml")},
        ],
    }


@pytest.mark.asyncio
async def test_envs_reports_missing_directory(project):
    (project / "mlclient-local.yaml").unlink()
    project.rmdir()
    with pytest.raises(ToolError, match="ml env init"):
        await mcp.call_tool("MLClientEnvs", {})


@pytest.mark.asyncio
async def test_tool_discovery_reports_code_capabilities_and_schemas():
    tools = {tool.name: tool for tool in await mcp.list_tools()}
    assert len(tools) == 13
    for name in ("Eval", "Estimate", "Uris", "Search", "Values", "Http"):
        tool = tools["MLClient" + name]
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is True
        assert tool.annotations.idempotentHint is False
        assert tool.annotations.openWorldHint is True
        assert tool.outputSchema["type"] == "object"
    assert tools["MLClientDocs"].annotations.readOnlyHint is True
    schema = tools["MLClientSearch"].inputSchema["$defs"]["SearchInput"]
    assert "connection" in schema["properties"]
    assert "root_namespace" in schema["properties"]


@pytest.mark.asyncio
async def test_version_uses_named_connection(mocker):
    version = mocker.patch.object(AsyncMLClient, "version", return_value="12.0.1")
    factory = mocker.spy(MLClientManager, "get_async_client")
    assert await call(
        "MLClientVersion",
        environment=" local ",
        connection=" alternate ",
    ) == {
        "environment": "local",
        "version": "12.0.1",
    }
    factory.assert_called_once_with(mocker.ANY, "alternate")
    assert factory.spy_return.http.base_url == "http://localhost:8101"
    version.assert_awaited_once()


@pytest.mark.parametrize("language", ["xquery", "javascript"])
@pytest.mark.asyncio
async def test_eval_preserves_code_variables_and_database(mocker, language):
    evaluate = mocker.patch.object(AsyncEvalService, language, return_value=3)
    code = "  1 + 2\n"
    assert await call(
        "MLClientEval",
        environment="local",
        code=code,
        language=language,
        variables={"x": 1},
        database="Documents",
    ) == {"environment": "local", "result": 3}
    evaluate.assert_awaited_once_with(code, variables={"x": 1}, database="Documents")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ([], []),
        (3, 3),
        (b"\x00\xff", {"encoding": "base64", "data": "AP8="}),
        (ElemTree.fromstring("<root>one</root>"), "<root>one</root>"),
        (
            ElemTree.ElementTree(ElemTree.fromstring("<root>one</root>")),
            "<root>one</root>",
        ),
        (
            {"nested": [b"x", Decimal("1.25")]},
            {"nested": [{"encoding": "base64", "data": "eA=="}, "1.25"]},
        ),
        (datetime(2026, 10, 5, tzinfo=timezone.utc), "2026-10-05 00:00:00+00:00"),
    ],
)
@pytest.mark.asyncio
async def test_eval_serializes_parsed_values_losslessly(mocker, value, expected):
    mocker.patch.object(AsyncEvalService, "xquery", return_value=value)
    assert (await call("MLClientEval", environment="local", code="()"))[
        "result"
    ] == expected


@pytest.mark.asyncio
async def test_eval_rejects_oversized_output(mocker):
    mocker.patch.object(AsyncEvalService, "xquery", return_value="x" * 200001)
    with pytest.raises(ToolError, match="reduce page_size"):
        await call("MLClientEval", environment="local", code="()")


@pytest.mark.asyncio
@respx.mock
async def test_eval_uses_real_transport_and_named_connection():
    # Empty sequences are a real /v1/eval response without multipart content.
    route = respx.post("http://localhost:8101/v1/eval").respond(200)
    assert await call(
        "MLClientEval",
        environment="local",
        connection="alternate",
        code="()",
    ) == {
        "environment": "local",
        "result": [],
    }
    assert route.calls.last.request.content == b"xquery=%28%29"


@pytest.mark.parametrize(
    ("tool", "fields"),
    [
        ("Version", {}),
        ("Health", {}),
        ("Eval", {"code": "1"}),
        ("Estimate", {}),
        ("Uris", {}),
        ("Search", {}),
        ("Values", {"reference": "cts:path-reference('/a')"}),
        ("Docs", {"uris": ["/a"]}),
        ("Logs", {}),
        ("Indexes", {"database": "Documents"}),
        ("DbStatus", {"database": "Documents"}),
        ("Http", {"endpoint": "/v1/ping"}),
    ],
)
@pytest.mark.asyncio
async def test_tools_report_missing_environment(tool, fields):
    with pytest.raises(ToolError, match="MLClientEnvs"):
        await call("MLClient" + tool, environment="missing", **fields)


@pytest.mark.asyncio
async def test_eval_reports_service_error_as_tool_error(mocker):
    mocker.patch.object(
        AsyncEvalService,
        "xquery",
        side_effect=ValueError("synthetic failure"),
    )
    with pytest.raises(ToolError, match="ValueError: synthetic failure"):
        await call("MLClientEval", environment="local", code="()")


@pytest.mark.parametrize(
    ("tool", "params"),
    [
        ("Version", {"environment": " "}),
        ("Version", {"environment": "local", "connection": " "}),
        ("Version", {"environment": "local", "unknown": True}),
        ("Uris", {"environment": "local", "page_size": 1001}),
        ("Search", {"environment": "local", "start": 0}),
        ("Docs", {"environment": "local", "uris": []}),
        ("Docs", {"environment": "local", "uris": ["/a"] * 101}),
        ("Docs", {"environment": "local", "uris": ["/a"], "max_chars": 99}),
        ("Logs", {"environment": "local", "limit": 1001}),
        ("Http", {"environment": "local", "endpoint": "https://example.com/"}),
        ("Http", {"environment": "local", "endpoint": "//example.com/"}),
        ("Http", {"environment": "local", "endpoint": "/v1/ping#fragment"}),
    ],
)
@pytest.mark.asyncio
async def test_tool_validation_rejects_invalid_input(tool, params):
    with pytest.raises(ToolError, match="validation error"):
        await call("MLClient" + tool, **params)


@pytest.mark.asyncio
async def test_health_does_not_require_rest_configuration(project, mocker):
    (project / "mlclient-local.yaml").write_text(
        "app-name: health-only\nhost: localhost\n",
    )
    health = mocker.patch.object(AsyncMLClient, "healthcheck", return_value=True)
    assert await call("MLClientHealth", environment="local") == {
        "environment": "local",
        "healthy": True,
    }
    health.assert_awaited_once()


@pytest.mark.parametrize("first", [False, httpx.ConnectError("synthetic unavailable")])
@pytest.mark.asyncio
async def test_health_wait_retries_until_ready(mocker, first):
    mocker.patch.object(AsyncMLClient, "healthcheck", side_effect=[first, True])
    mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)
    assert await call("MLClientHealth", environment="local", wait=True) == {
        "environment": "local",
        "healthy": True,
        "attempts": 2,
        "timed_out": False,
    }


@pytest.mark.asyncio
async def test_health_wait_bounds_slow_request(mocker):
    cancelled = asyncio.Event()

    async def slow_probe():
        try:
            await asyncio.sleep(30)
        finally:
            cancelled.set()

    mocker.patch.object(AsyncMLClient, "healthcheck", side_effect=slow_probe)
    result = await asyncio.wait_for(
        call(
            "MLClientHealth",
            environment="local",
            wait=True,
            timeout_seconds=1,
        ),
        timeout=2,
    )
    assert result == {
        "environment": "local",
        "healthy": False,
        "attempts": 1,
        "timed_out": True,
    }
    assert cancelled.is_set()


@pytest.mark.parametrize("tool", ["Estimate", "Uris", "Search"])
@pytest.mark.asyncio
async def test_query_tools_bind_namespaced_root_and_filter_search(mocker, tool):
    evaluate = mocker.patch.object(
        AsyncEvalService,
        "xquery",
        return_value={"results": [], "total": 0}
        if tool == "Search"
        else 0
        if tool == "Estimate"
        else [],
    )
    await call(
        "MLClient" + tool,
        environment="local",
        document_root="order",
        root_namespace="urn:orders",
    )
    code = evaluate.call_args.args[0]
    expected = resources_utils.read_test_resource_text(
        __file__,
        tool.lower() + ".xqy",
    ).removesuffix("\n")
    assert code == expected
    assert evaluate.call_args.kwargs == {
        "variables": {"root": "order", "root_namespace": "urn:orders"},
        "database": None,
    }


@pytest.mark.parametrize(
    ("tool", "value", "key", "expected"),
    [
        ("Estimate", 3, "estimate", 3),
        ("Uris", "/one.xml", "uris", ["/one.xml"]),
        ("Uris", None, "uris", []),
        ("Uris", ["/one.xml", "/two.xml"], "uris", ["/one.xml", "/two.xml"]),
    ],
)
@pytest.mark.asyncio
async def test_query_tools_normalize_results_without_root(
    mocker,
    tool,
    value,
    key,
    expected,
):
    evaluate = mocker.patch.object(AsyncEvalService, "xquery", return_value=value)
    assert (await call("MLClient" + tool, environment="local", database="Documents"))[
        key
    ] == expected
    assert evaluate.call_args.kwargs == {"variables": None, "database": "Documents"}
    assert "$root" not in evaluate.call_args.args[0]


@pytest.mark.asyncio
async def test_values_preserves_reference_query_and_limit(mocker):
    evaluate = mocker.patch.object(
        AsyncEvalService,
        "xquery",
        return_value=["open", "closed"],
    )
    assert await call(
        "MLClientValues",
        environment="local",
        reference='cts:path-reference("/order/status")',
        limit=2,
    ) == {
        "environment": "local",
        "values": ["open", "closed"],
    }
    assert evaluate.call_args.args[0] == (
        'cts:values(cts:path-reference("/order/status"), (), '
        '("frequency-order", "descending", "limit=2"), cts:true-query())'
    )


@pytest.mark.parametrize("as_mapping", [False, True])
@pytest.mark.asyncio
async def test_docs_preserves_content_and_metadata(mocker, as_mapping):
    document = Document.json(
        "/a.json",
        {"key": 1},
        metadata=Metadata(collections=["orders"]),
    )
    read = mocker.patch.object(
        AsyncDocumentsService,
        "read",
        return_value={"/a.json": document} if as_mapping else document,
    )
    result = await call(
        "MLClientDocs",
        environment="local",
        uris=["/a.json"],
        category=["content", "metadata"],
        database="Documents",
    )
    assert result["documents"][0] == {
        "uri": "/a.json",
        "docType": "json",
        "content": {"key": 1},
        "metadata": document.metadata.to_json(),
        "truncated": False,
    }
    read.assert_awaited_once_with(
        ["/a.json"],
        category=["content", "metadata"],
        database="Documents",
    )


@pytest.mark.asyncio
async def test_docs_supports_metadata_only_and_binary(mocker):
    metadata = Metadata(collections=["orders"])
    documents = {
        "/metadata": Document.metadata_update("/metadata", metadata),
        "/binary": Document.binary("/binary", b"\x00\xff"),
    }
    mocker.patch.object(AsyncDocumentsService, "read", return_value=documents)
    result = await call("MLClientDocs", environment="local", uris=list(documents))
    assert result["documents"][0]["metadata"] == metadata.to_json()
    assert result["documents"][0]["content"] is None
    assert result["documents"][0]["docType"] is None
    assert result["documents"][1]["content"] == {"encoding": "base64", "data": "AP8="}


@pytest.mark.asyncio
async def test_docs_marks_truncated_preview(mocker):
    document = Document.text("/a.txt", "x" * 101)
    mocker.patch.object(
        AsyncDocumentsService,
        "read",
        return_value={"/a.txt": document},
    )
    result = await call(
        "MLClientDocs",
        environment="local",
        uris=["/a.txt"],
        max_chars=100,
    )
    assert result["documents"][0]["content"] == "x" * 100
    assert result["documents"][0]["truncated"] is True


@pytest.mark.parametrize("limit", [1, 100])
@pytest.mark.asyncio
async def test_logs_forwards_filters_and_limits_latest_entries(mocker, limit):
    entries = [
        {"timestamp": f"2026-10-05T08:00:0{i}Z", "message": str(i)} for i in range(3)
    ]
    get = mocker.patch.object(AsyncLogsService, "get", return_value=iter(entries))
    result = await call(
        "MLClientLogs",
        environment="local",
        app_server="8100",
        start_time="2026-10-05T08:00:00Z",
        regex="Error",
        host="node-a",
        limit=limit,
    )
    assert result == {
        "environment": "local",
        "logs": entries[-limit:],
        "total": 3,
        "truncated": limit < 3,
    }
    get.assert_awaited_once_with(
        app_server="8100",
        log_type="error",
        start_time="2026-10-05T08:00:00Z",
        end_time=None,
        regex="Error",
        host="node-a",
    )


@pytest.mark.parametrize("extra", [{"log_type": "access"}, {"host": "node-a"}])
@pytest.mark.asyncio
async def test_logs_rejects_invalid_all_hosts_combination(extra):
    with pytest.raises(ToolError, match="all_hosts supports"):
        await call("MLClientLogs", environment="local", all_hosts=True, **extra)


@pytest.mark.asyncio
async def test_logs_merges_hosts_by_timestamp(mocker):
    hosts = resources_utils.get_test_resource_json(__file__, "hosts.json")
    names = [
        item["nameref"]
        for item in hosts["host-default-list"]["list-items"]["list-item"]
    ]
    mocker.patch.object(
        AsyncHostsApi,
        "get_list",
        return_value=httpx.Response(200, json=hosts),
    )

    async def get(**kwargs):
        index = names.index(kwargs["host"])
        return iter(
            [{"timestamp": f"2026-10-05T08:00:0{1 - index}Z", "message": "entry"}],
        )

    mocker.patch.object(AsyncLogsService, "get", side_effect=get)
    result = await call("MLClientLogs", environment="local", all_hosts=True)
    assert [entry["host"] for entry in result["logs"]] == names[::-1]
    assert result["total"] == 2


@pytest.mark.parametrize("operation", ["Indexes", "DbStatus"])
@pytest.mark.asyncio
async def test_database_tools_use_management_api(mocker, operation):
    properties = resources_utils.get_test_resource_json(
        __file__,
        "database-properties.json",
    )
    method = "get_properties" if operation == "Indexes" else "get"
    api = mocker.patch.object(
        AsyncDatabasesApi,
        method,
        return_value=httpx.Response(200, json=properties),
    )
    result = await call(
        "MLClient" + operation,
        environment="local",
        database="Documents",
    )
    assert result["environment"] == "local"
    assert result["database"] == "Documents"
    if operation == "Indexes":
        assert result["indexes"] == {
            key: value
            for key, value in properties.items()
            if key
            in (
                "range-element-index",
                "range-element-attribute-index",
                "range-path-index",
                "range-field-index",
            )
        }
        api.assert_awaited_once_with("Documents", data_format="json")
    else:
        assert result["status"] == properties
        api.assert_awaited_once_with("Documents", view="status", data_format="json")


@pytest.mark.parametrize(
    ("status", "body"),
    [(200, {"ok": True}), (404, {"error": "synthetic"}), (204, "")],
)
@pytest.mark.asyncio
async def test_http_exposes_status_and_body_and_preserves_request(mocker, status, body):
    response = (
        httpx.Response(status, json=body)
        if isinstance(body, dict)
        else httpx.Response(status, text=body)
    )
    request = mocker.patch.object(AsyncHttpClient, "request", return_value=response)
    assert await call(
        "MLClientHttp",
        environment="local",
        method="POST",
        endpoint="/v1/search",
        body="  raw body\n",
        headers={"X-Test": "a"},
        params={"q": "x"},
    ) == {
        "environment": "local",
        "status": status,
        "body": body,
    }
    request.assert_awaited_once_with(
        "POST",
        "/v1/search",
        body="  raw body\n",
        params={"q": "x"},
        headers={"X-Test": "a"},
    )


@pytest.mark.asyncio
async def test_stdio_protocol_reports_structured_success_and_real_error(project):
    async with (
        stdio_client(
            StdioServerParameters(
                command=sys.executable,
                args=["-m", "mlclient.mcp"],
                cwd=str(project.parent),
            ),
        ) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool("MLClientEnvs", {})
        assert result.isError is False
        assert result.structuredContent["count"] == 1
        result = await session.call_tool(
            "MLClientVersion",
            {"params": {"environment": "missing"}},
        )
        assert result.isError is True
        assert "MLClientEnvs" in result.content[0].text


def test_main_uses_stdio(mocker):
    run = mocker.patch.object(mcp, "run")
    main()
    run.assert_called_once_with()


@pytest.mark.asyncio
async def test_version_accepts_explicit_default_connection(mocker):
    mocker.patch.object(AsyncMLClient, "version", return_value="12.0.1")
    assert (await call("MLClientVersion", environment="local", connection=None))[
        "version"
    ] == "12.0.1"


@pytest.mark.asyncio
async def test_logs_cancels_other_hosts_before_reporting_failure(mocker):
    hosts = resources_utils.get_test_resource_json(__file__, "hosts.json")
    names = [
        item["nameref"]
        for item in hosts["host-default-list"]["list-items"]["list-item"]
    ]
    mocker.patch.object(
        AsyncHostsApi,
        "get_list",
        return_value=httpx.Response(200, json=hosts),
    )
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def get(**kwargs):
        if kwargs["host"] == names[0]:
            await started.wait()
            message = "synthetic host failure"
            raise httpx.ConnectError(message)
        started.set()
        try:
            await asyncio.sleep(30)
        finally:
            cancelled.set()

    mocker.patch.object(AsyncLogsService, "get", side_effect=get)
    with pytest.raises(ToolError, match="synthetic host failure"):
        await call("MLClientLogs", environment="local", all_hosts=True)
    assert cancelled.is_set()


@pytest.mark.asyncio
@respx.mock
async def test_management_connection_override_reaches_selected_server():
    properties = resources_utils.get_test_resource_json(
        __file__,
        "database-properties.json",
    )
    route = respx.get(
        "http://localhost:8101/manage/v2/databases/Documents/properties",
        params={"format": "json"},
    ).respond(200, json=properties)
    result = await call(
        "MLClientIndexes",
        environment="local",
        connection="alternate",
        database="Documents",
    )
    assert result["database"] == "Documents"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_health_connection_override_reaches_selected_server():
    route = respx.head("http://localhost:8101/").respond(200)
    assert (await call("MLClientHealth", environment="local", connection="alternate"))[
        "healthy"
    ] is True
    assert route.called


@pytest.mark.parametrize(
    ("headers", "content_type", "expected_body"),
    [
        (None, "application/json", b'{"key": "value"}'),
        ({"content-type": "application/json"}, "application/json", b'{"key": "value"}'),
        (
            {"content-type": "application/x-www-form-urlencoded"},
            "application/x-www-form-urlencoded",
            b"key=value",
        ),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_http_dictionary_body_defaults_to_json_and_respects_explicit_header(
    headers, content_type, expected_body,
):
    route = respx.post("http://localhost:8100/v1/search").respond(204)
    result = await call(
        "MLClientHttp",
        environment="local",
        method="POST",
        endpoint="/v1/search",
        body={"key": "value"},
        headers=headers,
    )
    assert result == {"environment": "local", "status": 204, "body": ""}
    assert route.calls.last.request.headers["content-type"] == content_type
    assert route.calls.last.request.content == expected_body
