from __future__ import annotations

import json
import xml.etree.ElementTree as ElemTree
from types import SimpleNamespace

import httpx
import pytest

from mlclient.exceptions import (
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
)
from mlclient.mcp import server
from mlclient.mcp.server import (
    EvalInput,
    EvalLanguage,
    ml_client_envs,
    ml_client_eval,
    ml_client_health,
    ml_client_version,
)


class _FakeClient:
    def __init__(self, **attrs):
        for name, value in attrs.items():
            setattr(self, name, value)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _patch_manager(mocker, *, client=None, error=None):
    if error is not None:
        return mocker.patch(
            "mlclient.mcp.server.MLClientManager",
            side_effect=error,
        )
    manager = mocker.Mock()
    manager.get_async_client.return_value = client
    return mocker.patch(
        "mlclient.mcp.server.MLClientManager",
        return_value=manager,
    )


def test_dump_renders_xml_bytes_lists_and_scalars():
    element = ElemTree.Element("rn")
    element.text = "50-00-0"
    tree = ElemTree.ElementTree(ElemTree.fromstring("<n>1</n>"))

    assert json.loads(server._dump(3)) == 3
    assert json.loads(server._dump(b"abc")) == "abc"
    assert "<rn>50-00-0</rn>" in json.loads(server._dump(element))
    assert "<n>1</n>" in json.loads(server._dump(tree))
    assert json.loads(server._dump([1, b"x"])) == [1, "x"]


def test_error_messages_are_actionable():
    env_error = MLClientEnvironmentNotFoundError("missing env!")
    dir_error = MLClientDirectoryNotFoundError("no dir!")

    assert "MLClientEnvs" in server._error(env_error)
    assert "ml env init" in server._error(dir_error)
    assert server._error(ValueError("boom")) == "Error: ValueError: boom"


@pytest.mark.asyncio
async def test_envs_lists_configurations(mocker, tmp_path):
    directory = tmp_path / ".mlclient"
    directory.mkdir()
    (directory / "mlclient-local.yaml").write_text("host: localhost")
    (directory / "mlclient-dev.yaml").write_text("host: dev")
    mocker.patch(
        "mlclient.mcp.server.find_mlclient_directory",
        return_value=directory,
    )

    result = json.loads(await ml_client_envs())

    assert result["count"] == 2
    assert [env["name"] for env in result["environments"]] == ["dev", "local"]


@pytest.mark.asyncio
async def test_envs_without_directory_returns_actionable_error(mocker):
    mocker.patch(
        "mlclient.mcp.server.find_mlclient_directory",
        side_effect=MLClientDirectoryNotFoundError("none!"),
    )

    assert "ml env init" in await ml_client_envs()


@pytest.mark.asyncio
async def test_version_returns_environment_and_version(mocker):
    client = _FakeClient(version=mocker.AsyncMock(return_value="MarkLogic 12.0.1"))
    _patch_manager(mocker, client=client)

    params = server.EnvironmentInput(environment="local")
    result = json.loads(await ml_client_version(params))

    assert result == {"environment": "local", "version": "MarkLogic 12.0.1"}


@pytest.mark.asyncio
async def test_health_reports_boolean(mocker):
    client = _FakeClient(healthcheck=mocker.AsyncMock(return_value=True))
    _patch_manager(mocker, client=client)

    params = server.HealthInput(environment="local")
    result = json.loads(await ml_client_health(params))

    assert result == {"environment": "local", "healthy": True}


@pytest.mark.asyncio
async def test_health_wait_returns_on_first_healthy_response(mocker):
    healthcheck = mocker.AsyncMock(side_effect=[False, True])
    client = _FakeClient(healthcheck=healthcheck)
    _patch_manager(mocker, client=client)
    sleep = mocker.patch("mlclient.mcp.server.asyncio.sleep", mocker.AsyncMock())

    params = server.HealthInput(environment="local", wait=True, interval_seconds=1)
    result = json.loads(await ml_client_health(params))

    assert result == {
        "environment": "local",
        "healthy": True,
        "attempts": 2,
        "timed_out": False,
    }
    sleep.assert_awaited_once()


@pytest.mark.asyncio
async def test_wait_for_health_treats_transport_error_as_unhealthy(mocker):
    healthcheck = mocker.AsyncMock(side_effect=[httpx.ConnectError("down"), True])
    client = _FakeClient(healthcheck=healthcheck)
    mocker.patch("mlclient.mcp.server.asyncio.sleep", mocker.AsyncMock())

    result = await server._wait_for_health(
        client,
        interval_seconds=1,
        timeout_seconds=120,
    )

    assert result == {"healthy": True, "attempts": 2, "timed_out": False}


@pytest.mark.asyncio
async def test_wait_for_health_reports_timeout(mocker):
    client = _FakeClient(healthcheck=mocker.AsyncMock(return_value=False))
    sleep = mocker.patch("mlclient.mcp.server.asyncio.sleep", mocker.AsyncMock())

    result = await server._wait_for_health(
        client,
        interval_seconds=1,
        timeout_seconds=0,
    )

    assert result == {"healthy": False, "attempts": 1, "timed_out": True}
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_version_reports_connection_failure(mocker):
    _patch_manager(mocker, error=MLClientEnvironmentNotFoundError("no env for [prod]!"))

    result = await ml_client_version(server.EnvironmentInput(environment="prod"))

    assert "MLClientEnvs" in result


@pytest.mark.asyncio
async def test_health_reports_connection_failure(mocker):
    _patch_manager(mocker, error=MLClientDirectoryNotFoundError("none!"))

    result = await ml_client_health(server.HealthInput(environment="prod"))

    assert "ml env init" in result


@pytest.mark.asyncio
async def test_eval_xquery_passes_variables_and_database(mocker):
    xquery = mocker.AsyncMock(return_value=3)
    client = _FakeClient(
        eval=SimpleNamespace(xquery=xquery, javascript=mocker.AsyncMock()),
    )
    _patch_manager(mocker, client=client)

    result = await ml_client_eval(
        EvalInput(
            environment="local",
            code="xdmp:estimate(cts:search(fn:doc(),cts:true-query()))",
            variables={"x": 1},
            database="scifinder-content",
        ),
    )

    assert json.loads(result) == 3
    xquery.assert_awaited_once_with(
        "xdmp:estimate(cts:search(fn:doc(),cts:true-query()))",
        variables={"x": 1},
        database="scifinder-content",
    )


@pytest.mark.asyncio
async def test_eval_routes_javascript(mocker):
    javascript = mocker.AsyncMock(return_value="ok")
    client = _FakeClient(
        eval=SimpleNamespace(xquery=mocker.AsyncMock(), javascript=javascript),
    )
    _patch_manager(mocker, client=client)

    result = await ml_client_eval(
        EvalInput(environment="local", code="1", language=EvalLanguage.JAVASCRIPT),
    )

    assert json.loads(result) == "ok"
    javascript.assert_awaited_once()


@pytest.mark.asyncio
async def test_eval_reports_missing_environment(mocker):
    _patch_manager(mocker, error=MLClientEnvironmentNotFoundError("no env for [prod]!"))

    result = await ml_client_eval(EvalInput(environment="prod", code="1"))

    assert "MLClientEnvs" in result


def test_scoped_wraps_query_with_and_without_root():
    assert server._scoped("cts:true-query()", None) == "(cts:true-query())"
    assert server._scoped("cts:true-query()", "substance") == (
        "cts:and-query((cts:document-root-query(xs:QName($root)), (cts:true-query())))"
    )


def test_as_list_normalizes_list_none_and_scalar():
    assert server._as_list(["a", "b"]) == ["a", "b"]
    assert server._as_list(None) == []
    assert server._as_list("x") == ["x"]


def test_page_slice_renders_positional_predicate():
    assert server._page_slice(1, 10) == "[1 to 10]"
    assert server._page_slice(5, 3) == "[5 to 7]"


def test_root_vars_binds_root_when_present():
    assert server._root_vars("substance") == {"root": "substance"}
    assert server._root_vars(None) is None


def test_response_body_prefers_json_then_text():
    def _raise():
        raise ValueError("no")

    assert server._response_body(SimpleNamespace(json=lambda: {"a": 1})) == {"a": 1}
    assert server._response_body(SimpleNamespace(json=_raise, text="raw")) == "raw"


@pytest.mark.asyncio
async def test_estimate_scopes_query_to_document_root(mocker):
    xquery = mocker.AsyncMock(return_value=42)
    client = _FakeClient(
        eval=SimpleNamespace(xquery=xquery, javascript=mocker.AsyncMock()),
    )
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_estimate(
            server.EstimateInput(environment="local", document_root="substance"),
        ),
    )

    assert result == {"environment": "local", "estimate": 42}
    xquery.assert_awaited_once_with(
        "cts:estimate(cts:and-query((cts:document-root-query(xs:QName($root)), "
        "(cts:true-query()))))",
        variables={"root": "substance"},
        database=None,
    )


@pytest.mark.asyncio
async def test_estimate_without_root_leaves_query_unscoped(mocker):
    xquery = mocker.AsyncMock(return_value=3)
    client = _FakeClient(
        eval=SimpleNamespace(xquery=xquery, javascript=mocker.AsyncMock()),
    )
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_estimate(
            server.EstimateInput(
                environment="local",
                query='cts:word-query("x")',
                database="scifinder-content",
            ),
        ),
    )

    assert result == {"environment": "local", "estimate": 3}
    xquery.assert_awaited_once_with(
        'cts:estimate((cts:word-query("x")))',
        variables=None,
        database="scifinder-content",
    )


@pytest.mark.asyncio
async def test_uris_lists_matching_document_uris(mocker):
    xquery = mocker.AsyncMock(return_value=["/a.xml", "/b.xml"])
    client = _FakeClient(
        eval=SimpleNamespace(xquery=xquery, javascript=mocker.AsyncMock()),
    )
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_uris(
            server.UrisInput(environment="local", document_root="reaction"),
        ),
    )

    assert result == {"environment": "local", "uris": ["/a.xml", "/b.xml"]}
    xquery.assert_awaited_once_with(
        "cts:search(fn:collection(), "
        "cts:and-query((cts:document-root-query(xs:QName($root)), "
        '(cts:true-query()))), "unfiltered")[1 to 100] ! xdmp:node-uri(.)',
        variables={"root": "reaction"},
        database=None,
    )


@pytest.mark.asyncio
async def test_search_returns_page_and_total(mocker):
    payload = {
        "total": 7,
        "start": 1,
        "pageSize": 10,
        "results": [{"uri": "/a.xml", "document": "<a/>"}],
    }
    xquery = mocker.AsyncMock(return_value=payload)
    client = _FakeClient(
        eval=SimpleNamespace(xquery=xquery, javascript=mocker.AsyncMock()),
    )
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_search(
            server.SearchInput(environment="local", query='cts:word-query("pd")'),
        ),
    )

    assert result == {"environment": "local", **payload}
    code = xquery.await_args.args[0]
    assert code.startswith("object-node {")
    assert 'cts:estimate((cts:word-query("pd")))' in code
    assert '"start": 1' in code
    assert '"pageSize": 10' in code
    assert "[1 to 10]" in code
    assert "xdmp:quote(.)" in code


@pytest.mark.asyncio
async def test_values_reads_lexicon_by_frequency(mocker):
    xquery = mocker.AsyncMock(return_value=["open", "closed"])
    client = _FakeClient(
        eval=SimpleNamespace(xquery=xquery, javascript=mocker.AsyncMock()),
    )
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_values(
            server.ValuesInput(
                environment="local",
                reference='cts:element-reference(xs:QName("status"))',
            ),
        ),
    )

    assert result == {"environment": "local", "values": ["open", "closed"]}
    xquery.assert_awaited_once_with(
        'cts:values(cts:element-reference(xs:QName("status")), (), '
        '("frequency-order", "descending", "limit=100"), cts:true-query())',
        variables=None,
        database=None,
    )


@pytest.mark.asyncio
async def test_docs_reads_multiple_documents(mocker):
    documents = {
        "/a.xml": SimpleNamespace(
            uri="/a.xml",
            doc_type=SimpleNamespace(value="xml"),
            content="<a/>",
        ),
        "/b.json": SimpleNamespace(uri="/b.json", doc_type=None, content={"k": 1}),
    }
    read = mocker.AsyncMock(return_value=documents)
    client = _FakeClient(documents=SimpleNamespace(read=read))
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_docs(
            server.DocsInput(environment="local", uris=["/a.xml", "/b.json"]),
        ),
    )

    assert result["environment"] == "local"
    summaries = {document["uri"]: document for document in result["documents"]}
    assert summaries["/a.xml"] == {"uri": "/a.xml", "docType": "xml", "content": "<a/>"}
    assert summaries["/b.json"] == {
        "uri": "/b.json",
        "docType": None,
        "content": {"k": 1},
    }
    read.assert_awaited_once_with(
        ["/a.xml", "/b.json"],
        category=None,
        database=None,
    )


@pytest.mark.asyncio
async def test_docs_reads_single_document(mocker):
    document = SimpleNamespace(
        uri="/only.xml",
        doc_type=SimpleNamespace(value="xml"),
        content="<only/>",
    )
    read = mocker.AsyncMock(return_value=document)
    client = _FakeClient(documents=SimpleNamespace(read=read))
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_docs(
            server.DocsInput(
                environment="local",
                uris=["/only.xml"],
                category=["content"],
            ),
        ),
    )

    assert result["documents"] == [
        {"uri": "/only.xml", "docType": "xml", "content": "<only/>"},
    ]
    read.assert_awaited_once_with(
        ["/only.xml"],
        category=["content"],
        database=None,
    )


@pytest.mark.asyncio
async def test_logs_reads_single_host(mocker):
    entries = [{"timestamp": "2026-01-01T00:00:00", "message": "boom"}]
    get = mocker.AsyncMock(return_value=iter(entries))
    service = mocker.Mock()
    service.get = get
    mocker.patch("mlclient.mcp.server.AsyncLogsService", return_value=service)
    client = _FakeClient(manage=mocker.Mock())
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_logs(
            server.LogsInput(environment="local", app_server="3693", regex="boom"),
        ),
    )

    assert result == {"environment": "local", "logs": entries}
    get.assert_awaited_once_with(
        app_server="3693",
        log_type="error",
        start_time=None,
        end_time=None,
        regex="boom",
        host=None,
    )


@pytest.mark.asyncio
async def test_logs_aggregates_all_hosts_by_timestamp(mocker):
    hosts_response = SimpleNamespace(
        json=lambda: {
            "host-default-list": {
                "list-items": {
                    "list-item": [{"nameref": "host-a"}, {"nameref": "host-b"}],
                },
            },
        },
    )
    manage = mocker.Mock()
    manage.hosts.get_list = mocker.AsyncMock(return_value=hosts_response)
    mocker.patch("mlclient.mcp.server.MLResponseParser.raise_for_status")
    get = mocker.AsyncMock(
        side_effect=[
            iter([{"timestamp": "2026-01-01T00:00:02", "message": "a2"}]),
            iter([{"timestamp": "2026-01-01T00:00:01", "message": "b1"}]),
        ],
    )
    service = mocker.Mock()
    service.get = get
    mocker.patch("mlclient.mcp.server.AsyncLogsService", return_value=service)
    client = _FakeClient(manage=manage)
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_logs(
            server.LogsInput(environment="local", all_hosts=True),
        ),
    )

    assert result["logs"] == [
        {"timestamp": "2026-01-01T00:00:01", "message": "b1", "host": "host-b"},
        {"timestamp": "2026-01-01T00:00:02", "message": "a2", "host": "host-a"},
    ]


@pytest.mark.asyncio
async def test_logs_all_hosts_rejects_non_error_type(mocker):
    manager = _patch_manager(mocker, client=_FakeClient())

    result = await server.ml_client_logs(
        server.LogsInput(
            environment="local",
            all_hosts=True,
            log_type=server.LogKind.ACCESS,
        ),
    )

    assert "all_hosts supports the error log type only" in result
    manager.assert_not_called()


@pytest.mark.asyncio
async def test_indexes_filters_range_index_definitions(mocker):
    properties = {
        "range-element-index": [{"localname": "status"}],
        "range-path-index": [{"path-expression": "/a/b"}],
        "word-lexicon": ["x"],
    }
    manage = mocker.Mock()
    manage.databases.get_properties = mocker.AsyncMock(
        return_value=SimpleNamespace(json=lambda: properties),
    )
    mocker.patch("mlclient.mcp.server.MLResponseParser.raise_for_status")
    client = _FakeClient(manage=manage)
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_indexes(
            server.DatabaseInput(environment="local", database="scifinder-content"),
        ),
    )

    assert result == {
        "environment": "local",
        "database": "scifinder-content",
        "indexes": {
            "range-element-index": [{"localname": "status"}],
            "range-path-index": [{"path-expression": "/a/b"}],
        },
    }
    manage.databases.get_properties.assert_awaited_once_with(
        "scifinder-content",
        data_format="json",
    )


@pytest.mark.asyncio
async def test_db_status_returns_runtime_status(mocker):
    status = {"status-properties": {"enabled": True}}
    manage = mocker.Mock()
    manage.databases.get = mocker.AsyncMock(
        return_value=SimpleNamespace(json=lambda: status),
    )
    mocker.patch("mlclient.mcp.server.MLResponseParser.raise_for_status")
    client = _FakeClient(manage=manage)
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_db_status(
            server.DatabaseInput(environment="local", database="scifinder-content"),
        ),
    )

    assert result == {
        "environment": "local",
        "database": "scifinder-content",
        "status": status,
    }
    manage.databases.get.assert_awaited_once_with(
        "scifinder-content",
        view="status",
        data_format="json",
    )


@pytest.mark.asyncio
async def test_http_returns_status_and_json_body(mocker):
    response = SimpleNamespace(status_code=200, json=lambda: {"ok": True})
    request = mocker.AsyncMock(return_value=response)
    client = _FakeClient(http=SimpleNamespace(request=request))
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_http(
            server.HttpInput(
                environment="local",
                method=server.HttpMethod.POST,
                endpoint="/v1/search",
                body={"q": "x"},
                params={"format": "json"},
                headers={"X": "1"},
            ),
        ),
    )

    assert result == {"environment": "local", "status": 200, "body": {"ok": True}}
    request.assert_awaited_once_with(
        "POST",
        "/v1/search",
        body={"q": "x"},
        params={"format": "json"},
        headers={"X": "1"},
    )


@pytest.mark.asyncio
async def test_http_falls_back_to_text_body(mocker):
    response = SimpleNamespace(
        status_code=204,
        json=mocker.Mock(side_effect=ValueError),
        text="plain text",
    )
    request = mocker.AsyncMock(return_value=response)
    client = _FakeClient(http=SimpleNamespace(request=request))
    _patch_manager(mocker, client=client)

    result = json.loads(
        await server.ml_client_http(
            server.HttpInput(environment="local", endpoint="/v1/ping"),
        ),
    )

    assert result == {"environment": "local", "status": 204, "body": "plain text"}


@pytest.mark.parametrize(
    ("tool", "params"),
    [
        (server.ml_client_estimate, server.EstimateInput(environment="prod")),
        (server.ml_client_uris, server.UrisInput(environment="prod")),
        (server.ml_client_search, server.SearchInput(environment="prod")),
        (
            server.ml_client_values,
            server.ValuesInput(environment="prod", reference="r"),
        ),
        (server.ml_client_docs, server.DocsInput(environment="prod", uris=["/a"])),
        (server.ml_client_logs, server.LogsInput(environment="prod")),
        (
            server.ml_client_indexes,
            server.DatabaseInput(environment="prod", database="d"),
        ),
        (
            server.ml_client_db_status,
            server.DatabaseInput(environment="prod", database="d"),
        ),
        (server.ml_client_http, server.HttpInput(environment="prod", endpoint="/x")),
    ],
)
@pytest.mark.asyncio
async def test_data_tools_report_connection_failure(mocker, tool, params):
    _patch_manager(mocker, error=MLClientEnvironmentNotFoundError("no env for [prod]!"))

    assert "MLClientEnvs" in await tool(params)


def test_main_runs_server_over_stdio(mocker):
    run = mocker.patch.object(server.mcp, "run")

    server.main()

    run.assert_called_once_with()
