"""The MCP server module exposing MarkLogic operations through mlclient.

This module builds a FastMCP server whose tools wrap mlclient's asynchronous
API. Every tool resolves its connection from a named mlclient environment
(``.mlclient/mlclient-<environment>.yaml`` located by walking up from the
server's working directory), so callers pass an environment name rather than a
host, port or credentials.

It exports the following:

    * mcp
        The configured FastMCP server instance.
    * main
        An entry point running the server over stdio transport.
"""

from __future__ import annotations

import asyncio
import base64
import heapq
import json
import xml.etree.ElementTree as ElemTree
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Any

from dateutil.parser import isoparse
from httpx import Headers, TransportError
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from mlclient._client import AsyncMLClient
from mlclient._manager import MLClientManager
from mlclient.env import find_mlclient_directory
from mlclient.exceptions import (
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
)
from mlclient.models import Metadata
from mlclient.responses import MLResponseParser
from mlclient.services.diagnostics import AsyncLogsService

mcp = FastMCP("mlclient_mcp")

_ENV_FILE_PATTERN = "mlclient-*.yaml"
_ENV_NAME_PREFIX = "mlclient-"
_MAX_RESULT_CHARS = 200000

_READ_ONLY_HINTS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

_CODE_HINTS = {
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": True,
}

_RANGE_INDEX_KEYS = (
    "range-element-index",
    "range-element-attribute-index",
    "range-path-index",
    "range-field-index",
)


class EvalLanguage(str, Enum):
    """A query language accepted by the eval tool."""

    XQUERY = "xquery"
    JAVASCRIPT = "javascript"


class LogKind(str, Enum):
    """A MarkLogic log file kind."""

    ERROR = "error"
    ACCESS = "access"
    REQUEST = "request"
    AUDIT = "audit"


class HttpMethod(str, Enum):
    """An HTTP method accepted by the raw passthrough tool."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"


class EnvironmentInput(BaseModel):
    """Input selecting a single mlclient environment."""

    model_config = ConfigDict(extra="forbid")

    environment: str = Field(
        ...,
        description=(
            "mlclient environment name resolving to "
            ".mlclient/mlclient-<environment>.yaml (e.g. 'local', 'dev'). "
            "Use MLClientEnvs to discover configured names."
        ),
        min_length=1,
    )

    connection: str | None = Field(
        default=None,
        description="Configured app-server identifier; defaults depend on the tool",
        min_length=1,
    )

    @field_validator("environment", "connection")
    @classmethod
    def validate_selector(cls, value: str | None) -> str | None:
        """Normalize configuration selectors, rejecting blank names.

        Parameters
        ----------
        value : str or None
            Environment or connection name.

        Returns
        -------
        str or None
            Stripped selector, or None for default connection selection.

        Raises
        ------
        ValueError
            If a selector contains only whitespace.
        """
        if value is None:
            return None
        value = value.strip()
        if not value:
            message = "environment and connection names cannot be blank"
            raise ValueError(message)
        return value


class HealthInput(EnvironmentInput):
    """Input for a MarkLogic health check, optionally waiting for readiness."""

    wait: bool = Field(
        default=False,
        description=(
            "Poll until the server is healthy instead of checking once; useful "
            "while waiting for a starting or restarting server"
        ),
    )
    interval_seconds: float = Field(
        default=5,
        description="Seconds between polls when wait=true",
        ge=1,
        le=60,
    )
    timeout_seconds: float = Field(
        default=120,
        description="Maximum total seconds to wait before giving up when wait=true",
        ge=1,
        le=600,
    )


class EvalInput(EnvironmentInput):
    """Input for evaluating XQuery or JavaScript on MarkLogic."""

    code: str = Field(
        ...,
        description="XQuery or JavaScript source to evaluate on the server",
        min_length=1,
    )
    language: EvalLanguage = Field(
        default=EvalLanguage.XQUERY,
        description="Language of the code: 'xquery' (default) or 'javascript'",
    )
    variables: dict[str, Any] | None = Field(
        default=None,
        description="External variables bound in the query, by name",
    )
    database: str | None = Field(
        default=None,
        description=(
            "Target database name; defaults to the REST server's content database"
        ),
    )


class DatabaseTargetInput(EnvironmentInput):
    """Input selecting an environment and an optional target database."""

    database: str | None = Field(
        default=None,
        description=(
            "Target database name; defaults to the REST server's content database"
        ),
    )


class QueryInput(DatabaseTargetInput):
    """Input carrying a cts:query expression scoped to an optional document root."""

    query: str = Field(
        default="cts:true-query()",
        description=(
            "XQuery cts:query expression (server-side code), e.g. "
            'cts:collection-query("x") or cts:word-query("palladium"); '
            "defaults to cts:true-query() which matches everything"
        ),
        min_length=1,
    )
    root_namespace: str = Field(
        default="",
        description="Namespace URI of document_root; empty selects no namespace",
    )
    document_root: str | None = Field(
        default=None,
        description=(
            "Local name of the document root element to scope to "
            "(e.g. 'substance', 'reaction'); omit to match across all roots"
        ),
    )


class EstimateInput(QueryInput):
    """Input for a fast, index-only fragment count via cts:estimate."""


class UrisInput(QueryInput):
    """Input for listing document URIs matching a query, with pagination."""

    start: int = Field(
        default=1,
        description="1-based index of the first URI to return",
        ge=1,
    )
    page_size: int = Field(
        default=100,
        description="Maximum number of URIs to return",
        ge=1,
        le=1000,
    )


class SearchInput(QueryInput):
    """Input for a paginated search returning matching documents and a total."""

    start: int = Field(
        default=1,
        description="1-based index of the first result to return",
        ge=1,
    )
    page_size: int = Field(
        default=10,
        description="Maximum number of documents to return",
        ge=1,
        le=100,
    )


class ValuesInput(DatabaseTargetInput):
    """Input for reading distinct lexicon values from a range index."""

    reference: str = Field(
        ...,
        description=(
            "XQuery cts:reference expression naming the range index to read, "
            'e.g. cts:element-reference(xs:QName("status")) or '
            'cts:path-reference("/doc/field")'
        ),
        min_length=1,
    )
    query: str = Field(
        default="cts:true-query()",
        description=(
            "XQuery cts:query expression constraining which documents "
            "contribute values; defaults to cts:true-query()"
        ),
        min_length=1,
    )
    limit: int = Field(
        default=100,
        description="Maximum number of values to return, by descending frequency",
        ge=1,
        le=10000,
    )


class DocsInput(DatabaseTargetInput):
    """Input for reading one or more documents by URI."""

    uris: list[str] = Field(
        ...,
        description="Document URIs to read",
        min_length=1,
        max_length=100,
    )
    category: list[str] | None = Field(
        default=None,
        description=(
            "Content categories to read (e.g. 'content', 'metadata'); "
            "omit to read document content"
        ),
    )

    max_chars: int = Field(
        default=20000,
        description="Maximum content characters per document; metadata is retained",
        ge=100,
        le=100000,
    )


class DatabaseInput(EnvironmentInput):
    """Input selecting an environment and a required database by name."""

    database: str = Field(
        ...,
        description="Database name to inspect",
        min_length=1,
    )


class LogsInput(EnvironmentInput):
    """Input for retrieving MarkLogic server logs."""

    app_server: str | None = Field(
        default=None,
        description=(
            "App server port whose logs to read (e.g. '3693'); "
            "omit for the system-wide log"
        ),
    )
    log_type: LogKind = Field(
        default=LogKind.ERROR,
        description="Log kind: 'error' (default), 'access', 'request' or 'audit'",
    )
    start_time: str | None = Field(
        default=None,
        description="ISO 8601 start time; filters error logs only",
    )
    end_time: str | None = Field(
        default=None,
        description="ISO 8601 end time; filters error logs only",
    )
    regex: str | None = Field(
        default=None,
        description="Regex filtering matching log lines; error logs only",
    )
    host: str | None = Field(
        default=None,
        description="Host name whose logs to read; omit for a single-host read",
    )
    all_hosts: bool = Field(
        default=False,
        description=(
            "Aggregate error logs from every cluster host, merged by timestamp "
            "and tagged with their host (like 'ml logs --all-hosts'). Supports "
            "the error log type only and cannot be combined with 'host'"
        ),
    )

    limit: int = Field(
        default=100,
        description="Maximum latest log entries returned, after filtering",
        ge=1,
        le=1000,
    )


class HttpInput(EnvironmentInput):
    """Input for a raw HTTP request against the environment's primary server."""

    method: HttpMethod = Field(
        default=HttpMethod.GET,
        description="HTTP method",
    )
    endpoint: str = Field(
        ...,
        description="Request path on the primary app server, e.g. '/v1/config/query'",
        min_length=1,
    )
    params: dict[str, Any] | None = Field(
        default=None,
        description="Query-string parameters",
    )
    body: str | dict[str, Any] | None = Field(
        default=None,
        description="Dict body defaults to JSON; Content-Type can override it",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Request headers",
    )

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        """Require a path on the selected server, without a URL fragment.

        Parameters
        ----------
        value : str
            Request endpoint supplied by the caller.

        Returns
        -------
        str
            The unchanged path.

        Raises
        ------
        ValueError
            If the endpoint is not an absolute server path or has a fragment.
        """
        if not value.startswith("/") or value.startswith("//") or "#" in value:
            message = "endpoint must be an absolute server path without a fragment"
            raise ValueError(message)
        return value


@asynccontextmanager
async def _connect(
    environment: str,
    connection: str | None = None,
    *,
    tier: str | None = None,
) -> AsyncIterator[AsyncMLClient]:
    """Yield a connected async client for a named mlclient environment.

    Parameters
    ----------
    environment : str
        An mlclient environment name selecting its configuration file.
    connection : str or None
        Configured server identifier; None selects the default for this tool.
    tier : str or None
        Bind manage/health to the selected connection instead of auxiliary defaults.

    Yields
    ------
    AsyncMLClient
        A connected client bound to the selected environment server.
    """
    manager = MLClientManager(environment)
    if tier is None:
        client = manager.get_async_client(connection)
    else:
        config = manager.get_config(connection or tier)
        client = AsyncMLClient(config=config, **{f"{tier}_config": config})
    async with client:
        yield client


async def _wait_for_health(
    client: AsyncMLClient,
    interval_seconds: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Poll a client's health check until it succeeds or the deadline passes.

    A transport failure counts as not-yet-healthy so polling survives a server
    that has not started listening. Polling stops on the first healthy response
    or once the timeout elapses, whichever comes first.

    Parameters
    ----------
    client : AsyncMLClient
        A connected client whose health server is polled.
    interval_seconds : float
        Seconds to sleep between polls, capped by the remaining time.
    timeout_seconds : float
        Maximum total seconds to keep polling.

    Returns
    -------
    dict
        ``{"healthy": bool, "attempts": int, "timed_out": bool}`` where
        ``timed_out`` is True only when the deadline passed while unhealthy.
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_seconds
    attempts = 0
    while True:
        remaining = deadline - loop.time()
        attempts += 1
        try:
            healthy = await asyncio.wait_for(client.healthcheck(), timeout=remaining)
        except (TransportError, asyncio.TimeoutError):
            healthy = False
        remaining = deadline - loop.time()
        if healthy or remaining <= 0:
            return {
                "healthy": bool(healthy),
                "attempts": attempts,
                "timed_out": not healthy,
            }
        await asyncio.sleep(min(interval_seconds, remaining))


def _to_jsonable(value: Any) -> Any:
    """Convert a parsed MarkLogic value into a JSON-serializable form.

    Parameters
    ----------
    value : Any
        A value returned by MLResponseParser (scalar, dict, XML node, bytes or
        a list of such items).

    Returns
    -------
    Any
        The value with XML nodes rendered as strings and bytes encoded as base64;
        lists are converted item by item and other values pass through.
    """
    if isinstance(value, ElemTree.ElementTree):
        value = value.getroot()
    if isinstance(value, ElemTree.Element):
        return ElemTree.tostring(value, encoding="unicode")
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode("ascii")}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


def _result(value: dict[str, Any]) -> dict[str, Any]:
    """Normalize a structured result to JSON-compatible values.

    Parameters
    ----------
    value : Any
        A value to serialize; MarkLogic-specific types are normalized first.

    Returns
    -------
    dict
        A JSON-compatible dictionary, with Decimal and datetime rendered as strings.
    """
    serialized = json.dumps(_to_jsonable(value), ensure_ascii=False, default=str)
    if len(serialized) > _MAX_RESULT_CHARS:
        message = (
            "Result exceeds 200000 characters; reduce page_size, limit or max_chars, "
            "or request a smaller result with Eval/Http."
        )
        raise ToolError(message)
    return json.loads(serialized)


def _error(exc: Exception) -> str:
    """Render an exception as an actionable, agent-facing message.

    Parameters
    ----------
    exc : Exception
        An exception raised while serving a tool call.

    Returns
    -------
    str
        A single-line message prefixed with 'Error:' that names the problem and,
        for recognized configuration failures, suggests a next step.
    """
    if isinstance(exc, MLClientEnvironmentNotFoundError):
        return (
            f"Error: {exc} Call MLClientEnvs to list configured environments, "
            "or create .mlclient/mlclient-<name>.yaml with `ml env init <name>`."
        )
    if isinstance(exc, MLClientDirectoryNotFoundError):
        return (
            f"Error: {exc} No .mlclient directory was found from the working "
            "directory upward; run `ml env init <name>` in your project."
        )
    return f"Error: {type(exc).__name__}: {exc}"


async def _eval(
    environment: str,
    code: str,
    *,
    variables: dict[str, Any] | None = None,
    database: str | None = None,
    connection: str | None = None,
) -> Any:
    """Evaluate XQuery on an environment and return the parsed result.

    Parameters
    ----------
    environment : str
        An mlclient environment name selecting its configuration file.
    code : str
        XQuery source to evaluate on the server.
    variables : dict or None, optional
        External variables bound in the query, by name.
    database : str or None, optional
        Target database name; defaults to the REST content database.
    connection : str or None
        Configured app-server identifier.

    Returns
    -------
    Any
        The value parsed by mlclient from the server response.
    """
    if variables and "root" in variables:
        code = (
            "declare variable $root as xs:string external;\n"
            "declare variable $root_namespace as xs:string external;\n" + code
        )
    async with _connect(environment, connection) as client:
        return await client.eval.xquery(code, variables=variables, database=database)


def _scoped(query: str, document_root: str | None) -> str:
    """Wrap a cts:query expression, optionally scoping it to a document root.

    Parameters
    ----------
    query : str
        An XQuery cts:query expression.
    document_root : str or None
        A document root local name bound to the external variable ``$root``, or
        None to leave the query unscoped.

    Returns
    -------
    str
        A cts:query expression, AND-combined with a document-root query when a
        root is given.
    """
    if document_root is None:
        return "(" + query + ")"
    return (
        "cts:and-query(("
        "cts:document-root-query(fn:QName($root_namespace, $root)), "
        "(" + query + ")"
        "))"
    )


def _page_slice(start: int, page_size: int) -> str:
    """Render a 1-based positional predicate for a page of results.

    Parameters
    ----------
    start : int
        The 1-based index of the first item in the page.
    page_size : int
        The maximum number of items in the page.

    Returns
    -------
    str
        An XQuery positional predicate, e.g. ``[1 to 10]``.
    """
    return "[" + str(start) + " to " + str(start + page_size - 1) + "]"


def _root_vars(document_root: str | None, root_namespace: str) -> dict[str, str] | None:
    """Build the external-variable map binding a document root, if present.

    Parameters
    ----------
    document_root : str or None
        A document root local name, or None.
    root_namespace : str
        Namespace URI; an empty string selects unnamespaced roots.

    Returns
    -------
    dict or None
        ``{"root": document_root}`` when a root is given, otherwise None.
    """
    return (
        {"root": document_root, "root_namespace": root_namespace}
        if document_root is not None
        else None
    )


def _as_list(value: Any) -> list[Any]:
    """Normalize a parsed scalar-or-sequence result into a list.

    Parameters
    ----------
    value : Any
        A value that may be a list, a single item, or None.

    Returns
    -------
    list
        The value as a list: itself if already a list, an empty list for None,
        otherwise a single-element list.
    """
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _document_summary(document: Any, max_chars: int) -> dict[str, Any]:
    """Summarize a parsed Document as a JSON-serializable object.

    Parameters
    ----------
    document : Any
        A Document returned by the documents service.
    max_chars : int
        Maximum content size, in serialized characters.

    Returns
    -------
    dict
        URI, type, content, truncation flag and metadata in JSON-compatible form.
    """
    content = _to_jsonable(document.content)
    rendered = content if isinstance(content, str) else json.dumps(content, default=str)
    truncated = len(rendered) > max_chars
    metadata = document.metadata
    return {
        "uri": document.uri,
        "docType": document.doc_type.value if document.doc_type else None,
        "content": rendered[:max_chars] if truncated else content,
        "truncated": truncated,
        "metadata": metadata.to_json() if isinstance(metadata, Metadata) else metadata,
    }


def _response_body(response: Any) -> Any:
    """Return an HTTP response body as parsed JSON when possible, else text.

    Parameters
    ----------
    response : Any
        An httpx.Response.

    Returns
    -------
    Any
        The decoded JSON body, or the raw text when the body is not JSON.
    """
    try:
        return response.json()
    except ValueError:
        return response.text


async def _cluster_hosts(client: AsyncMLClient) -> list[str]:
    """Return every host name in the cluster via the Management API.

    Parameters
    ----------
    client : AsyncMLClient
        A connected client.

    Returns
    -------
    list[str]
        Host names as reported by /manage/v2/hosts.
    """
    response = await client.manage.hosts.get_list(data_format="json")
    MLResponseParser.raise_for_status(response)
    items = response.json()["host-default-list"]["list-items"].get("list-item", [])
    return [item["nameref"] for item in items]


async def _host_error_logs(
    service: AsyncLogsService,
    params: LogsInput,
    host: str,
) -> Iterator[dict]:
    """Fetch one host's error logs, tagging each entry with the host name.

    Parameters
    ----------
    service : AsyncLogsService
        The logs service bound to the environment's Management API.
    params : LogsInput
        The validated logs request supplying app server and filters.
    host : str
        The host whose error logs to read.

    Returns
    -------
    Iterator[dict]
        Error log entries sorted by timestamp, each carrying a ``host`` key.
    """
    entries = await service.get(
        app_server=params.app_server,
        log_type=LogKind.ERROR.value,
        start_time=params.start_time,
        end_time=params.end_time,
        regex=params.regex,
        host=host,
    )
    return ({**entry, "host": host} for entry in entries)


async def _all_hosts_error_logs(
    client: AsyncMLClient,
    service: AsyncLogsService,
    params: LogsInput,
) -> list[dict]:
    """Collect error logs from every cluster host, merged by timestamp.

    Parameters
    ----------
    client : AsyncMLClient
        A connected client used to discover cluster hosts.
    service : AsyncLogsService
        The logs service used to read each host's error logs.
    params : LogsInput
        The validated logs request supplying app server and filters.

    Returns
    -------
    list[dict]
        Host-tagged error log entries from all hosts, ordered by timestamp.
    """
    hosts = await _cluster_hosts(client)
    tasks = [
        asyncio.create_task(_host_error_logs(service, params, host)) for host in hosts
    ]
    try:
        per_host = await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    return list(heapq.merge(*per_host, key=lambda entry: isoparse(entry["timestamp"])))


@mcp.tool(
    name="MLClientEnvs",
    annotations={"title": "List MarkLogic environments", **_READ_ONLY_HINTS},
)
async def ml_client_envs() -> dict[str, Any]:
    """Discover mlclient environment names and paths from the working directory.

    The nearest .mlclient directory is searched from this directory upward.

    Returns
    -------
    dict
        Environment directory, count and configuration names/paths.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        directory = find_mlclient_directory(Path.cwd())
    except MLClientDirectoryNotFoundError as exc:
        raise ToolError(_error(exc)) from exc
    environments = [
        {"name": path.stem.removeprefix(_ENV_NAME_PREFIX), "file": str(path)}
        for path in sorted(directory.glob(_ENV_FILE_PATTERN))
    ]
    return _result(
        {
            "directory": str(directory),
            "count": len(environments),
            "environments": environments,
        },
    )


@mcp.tool(
    name="MLClientVersion",
    annotations={"title": "Read MarkLogic version", **_READ_ONLY_HINTS},
)
async def ml_client_version(params: EnvironmentInput) -> dict[str, Any]:
    """Read the MarkLogic version for an environment.

    Uses the selected connection, or the first configured REST connection.

    Parameters
    ----------
    params : EnvironmentInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment name and server version.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        async with _connect(params.environment, params.connection) as client:
            version = await client.version()
        return _result({"environment": params.environment, "version": str(version)})
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientHealth",
    annotations={"title": "Check MarkLogic health", **_READ_ONLY_HINTS},
)
async def ml_client_health(params: HealthInput) -> dict[str, Any]:
    """Check MarkLogic health once or wait for readiness.

    Defaults to the health connection. With wait=true, temporary transport
    failures are retried until healthy or the deadline expires. The deadline
    includes in-flight probes; an unhealthy timeout is a normal result.

    Parameters
    ----------
    params : HealthInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment and healthy flag; waits add attempts and timed_out.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        async with _connect(
            params.environment,
            params.connection,
            tier="health",
        ) as client:
            if params.wait:
                result = await _wait_for_health(
                    client,
                    params.interval_seconds,
                    params.timeout_seconds,
                )
            else:
                result = {"healthy": await client.healthcheck()}
        return _result({"environment": params.environment, **result})
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientEval",
    annotations={
        "title": "Evaluate XQuery or JavaScript",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ml_client_eval(params: EvalInput) -> dict[str, Any]:
    """Evaluate XQuery or JavaScript and return its parsed result.

    Runs arbitrary server-side code and may modify data or call external
    systems. XQuery external variables must be declared in the supplied code.

    Parameters
    ----------
    params : EvalInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment and result; XML is text and binary values are base64 objects.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        async with _connect(params.environment, params.connection) as client:
            if params.language is EvalLanguage.JAVASCRIPT:
                result = await client.eval.javascript(
                    params.code,
                    variables=params.variables,
                    database=params.database,
                )
            else:
                result = await client.eval.xquery(
                    params.code,
                    variables=params.variables,
                    database=params.database,
                )
        return _result({"environment": params.environment, "result": result})
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientEstimate",
    annotations={"title": "Estimate matching fragment count", **_CODE_HINTS},
)
async def ml_client_estimate(params: EstimateInput) -> dict[str, Any]:
    """Estimate matching fragments from the indexes.

    The query is an XQuery expression, not a restricted query language; it may
    modify data or call external systems. Root names are scoped to the supplied
    namespace URI, defaulting to no namespace. This is not an exact document count.

    Parameters
    ----------
    params : EstimateInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment and estimated fragment count.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        result = await _eval(
            params.environment,
            "cts:estimate(" + _scoped(params.query, params.document_root) + ")",
            variables=_root_vars(params.document_root, params.root_namespace),
            database=params.database,
            connection=params.connection,
        )
        return _result({"environment": params.environment, "estimate": result})
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientUris",
    annotations={"title": "List matching document URIs", **_CODE_HINTS},
)
async def ml_client_uris(params: UrisInput) -> dict[str, Any]:
    """Read a page of document URIs matching a CTS query.

    Uses filtered search. Pagination starts at 1. Query is arbitrary XQuery
    code and may modify data or call external systems. Pair with Docs to read
    the selected content.

    Parameters
    ----------
    params : UrisInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment and document URI list.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        result = await _eval(
            params.environment,
            "cts:search(fn:collection(), "
            + _scoped(params.query, params.document_root)
            + ', "filtered")'
            + _page_slice(params.start, params.page_size)
            + " ! xdmp:node-uri(.)",
            variables=_root_vars(params.document_root, params.root_namespace),
            database=params.database,
            connection=params.connection,
        )
        return _result({"environment": params.environment, "uris": _as_list(result)})
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientSearch",
    annotations={"title": "Search documents", **_CODE_HINTS},
)
async def ml_client_search(params: SearchInput) -> dict[str, Any]:
    """Search matching documents and return a page with an estimated total.

    Uses filtered search. The total is a fragment estimate independent of the
    page. Query is arbitrary XQuery code and may modify data or call external
    systems. Root selection includes its namespace URI.

    Parameters
    ----------
    params : SearchInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment, total, start, pageSize and results with URI/document text.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        scoped = _scoped(params.query, params.document_root)
        result = await _eval(
            params.environment,
            "object-node {"
            ' "total": cts:estimate(' + scoped + "),"
            ' "start": ' + str(params.start) + ","
            ' "pageSize": ' + str(params.page_size) + ","
            ' "results": array-node {'
            " cts:search(fn:collection(), "
            + scoped
            + ', "filtered")'
            + _page_slice(params.start, params.page_size)
            + ' ! object-node { "uri": xdmp:node-uri(.), "document": xdmp:quote(.) }'
            " }"
            "}",
            variables=_root_vars(params.document_root, params.root_namespace),
            database=params.database,
            connection=params.connection,
        )
        return _result({"environment": params.environment, **result})
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientValues",
    annotations={"title": "Read range-index values", **_CODE_HINTS},
)
async def ml_client_values(params: ValuesInput) -> dict[str, Any]:
    """Read distinct range-index values in descending frequency order.

    The reference names a configured range index. Query restricts contributing
    fragments. Both fields are arbitrary XQuery code and may modify data or
    call external systems.

    Parameters
    ----------
    params : ValuesInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment and a list of parsed lexicon values.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        result = await _eval(
            params.environment,
            "cts:values("
            + params.reference
            + ", (), "
            + '("frequency-order", "descending", "limit='
            + str(params.limit)
            + '"), '
            + params.query
            + ")",
            database=params.database,
            connection=params.connection,
        )
        return _result({"environment": params.environment, "values": _as_list(result)})
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientDocs",
    annotations={"title": "Read documents by URI", **_READ_ONLY_HINTS},
)
async def ml_client_docs(params: DocsInput) -> dict[str, Any]:
    """Read documents by URI, preserving requested metadata.

    Accepts up to 100 URIs. Content exceeding max_chars is returned as a
    preview with truncated=true. XML is text; binary content is base64.

    Parameters
    ----------
    params : DocsInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment and documents with URI, type, content, metadata and truncation.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        async with _connect(params.environment, params.connection) as client:
            documents = await client.documents.read(
                params.uris,
                category=params.category,
                database=params.database,
            )
        found = documents.values() if isinstance(documents, dict) else [documents]
        return _result(
            {
                "environment": params.environment,
                "documents": [
                    _document_summary(document, params.max_chars) for document in found
                ],
            },
        )
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientLogs",
    annotations={"title": "Read server logs", **_READ_ONLY_HINTS},
)
async def ml_client_logs(params: LogsInput) -> dict[str, Any]:
    """Read the latest log entries, optionally filtered or combined across hosts.

    Defaults to the manage connection. Time and regex filters apply to error
    logs only. all_hosts supports error logs and cannot be combined with host.
    Returns at most limit latest entries, in timestamp order for error logs;
    this bounds output, not log retrieval work.

    Parameters
    ----------
    params : LogsInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment, log entries, fetched total and truncation flag.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    if params.all_hosts and (
        params.host is not None or params.log_type is not LogKind.ERROR
    ):
        message = (
            "all_hosts supports the error log type only "
            "and cannot be combined with host."
        )
        raise ToolError(message)
    try:
        async with _connect(
            params.environment,
            params.connection,
            tier="manage",
        ) as client:
            service = AsyncLogsService(client.manage)
            if params.all_hosts:
                logs = await _all_hosts_error_logs(client, service, params)
            else:
                logs = list(
                    await service.get(
                        app_server=params.app_server,
                        log_type=params.log_type.value,
                        start_time=params.start_time,
                        end_time=params.end_time,
                        regex=params.regex,
                        host=params.host,
                    ),
                )
        return _result(
            {
                "environment": params.environment,
                "logs": logs[-params.limit :],
                "total": len(logs),
                "truncated": len(logs) > params.limit,
            },
        )
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientIndexes",
    annotations={"title": "List database range indexes", **_READ_ONLY_HINTS},
)
async def ml_client_indexes(params: DatabaseInput) -> dict[str, Any]:
    """Inspect the range indexes configured on a database.

    Defaults to the manage connection. Includes element, element-attribute,
    path and field range indexes.

    Parameters
    ----------
    params : DatabaseInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment, database and range-index definitions.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        async with _connect(
            params.environment,
            params.connection,
            tier="manage",
        ) as client:
            response = await client.manage.databases.get_properties(
                params.database,
                data_format="json",
            )
        MLResponseParser.raise_for_status(response)
        properties = response.json()
        return _result(
            {
                "environment": params.environment,
                "database": params.database,
                "indexes": {
                    key: properties[key]
                    for key in _RANGE_INDEX_KEYS
                    if key in properties
                },
            },
        )
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientDbStatus",
    annotations={"title": "Read database status", **_READ_ONLY_HINTS},
)
async def ml_client_db_status(params: DatabaseInput) -> dict[str, Any]:
    """Read database runtime status from the Management API.

    Defaults to the manage connection.

    Parameters
    ----------
    params : DatabaseInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment, database and the native status response.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        async with _connect(
            params.environment,
            params.connection,
            tier="manage",
        ) as client:
            response = await client.manage.databases.get(
                params.database,
                view="status",
                data_format="json",
            )
        MLResponseParser.raise_for_status(response)
        return _result(
            {
                "environment": params.environment,
                "database": params.database,
                "status": response.json(),
            },
        )
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


@mcp.tool(
    name="MLClientHttp",
    annotations={
        "title": "Send a raw HTTP request",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ml_client_http(params: HttpInput) -> dict[str, Any]:
    """Send a raw HTTP request to the selected connection.

    The default is the first REST connection. Endpoint must be an absolute
    server path. Dictionary bodies default to JSON. The request may modify data;
    HTTP error responses retain their status and body for inspection.

    Parameters
    ----------
    params : HttpInput
        Validated tool parameters; see the input schema for fields and defaults.

    Returns
    -------
    dict
        Environment, HTTP status and JSON or text response body.

    Raises
    ------
    ToolError
        For configuration, execution or output-size failures.
    """
    try:
        headers = params.headers
        if isinstance(params.body, dict):
            headers = Headers(headers)
            headers.setdefault("Content-Type", "application/json")
        async with _connect(params.environment, params.connection) as client:
            response = await client.http.request(
                params.method.value,
                params.endpoint,
                body=params.body,
                params=params.params,
                headers=headers,
            )
        return _result(
            {
                "environment": params.environment,
                "status": response.status_code,
                "body": _response_body(response),
            },
        )
    except Exception as exc:
        raise ToolError(_error(exc)) from exc


def main() -> None:
    """Run the MCP server over stdio transport."""
    mcp.run()
