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
import heapq
import json
import time
import xml.etree.ElementTree as ElemTree
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Any

from dateutil.parser import isoparse
from httpx import TransportError
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from mlclient import AsyncMLClient, MLClientManager
from mlclient.env import find_mlclient_directory
from mlclient.exceptions import (
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
)
from mlclient.responses import MLResponseParser
from mlclient.services.logs import AsyncLogsService

mcp = FastMCP("mlclient_mcp")

_ENV_FILE_PATTERN = "mlclient-*.yaml"
_ENV_NAME_PREFIX = "mlclient-"

_READ_ONLY_HINTS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
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

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    environment: str = Field(
        ...,
        description=(
            "mlclient environment name resolving to "
            ".mlclient/mlclient-<environment>.yaml (e.g. 'local', 'dev'). "
            "Use MLClientEnvs to discover configured names."
        ),
        min_length=1,
    )


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
    """Input for reading co-occurring lexicon values from a range index."""

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
    )
    category: list[str] | None = Field(
        default=None,
        description=(
            "Content categories to read (e.g. 'content', 'metadata'); "
            "omit to read document content"
        ),
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
        description="Request body; a dict is sent as JSON",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Request headers",
    )


@asynccontextmanager
async def _connect(environment: str) -> AsyncIterator[AsyncMLClient]:
    """Yield a connected async client for a named mlclient environment.

    Parameters
    ----------
    environment : str
        An mlclient environment name selecting its configuration file.

    Yields
    ------
    AsyncMLClient
        A connected client bound to the environment's first REST server.
    """
    async with MLClientManager(environment).get_async_client() as client:
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
    deadline = time.monotonic() + timeout_seconds
    attempts = 0
    while True:
        attempts += 1
        try:
            healthy = await client.healthcheck()
        except TransportError:
            healthy = False
        remaining = deadline - time.monotonic()
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
        The value with XML nodes rendered as strings and bytes decoded as UTF-8;
        lists are converted item by item and other values pass through.
    """
    if isinstance(value, ElemTree.ElementTree):
        value = value.getroot()
    if isinstance(value, ElemTree.Element):
        return ElemTree.tostring(value, encoding="unicode")
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value


def _dump(value: Any) -> str:
    """Serialize a value as an indented JSON string.

    Parameters
    ----------
    value : Any
        A value to serialize; MarkLogic-specific types are normalized first.

    Returns
    -------
    str
        An indented JSON representation, with Decimal and datetime rendered via
        their string form.
    """
    return json.dumps(
        _to_jsonable(value),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


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

    Returns
    -------
    Any
        The value parsed by mlclient from the server response.
    """
    async with _connect(environment) as client:
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
        "cts:document-root-query(xs:QName($root)), "
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


def _root_vars(document_root: str | None) -> dict[str, str] | None:
    """Build the external-variable map binding a document root, if present.

    Parameters
    ----------
    document_root : str or None
        A document root local name, or None.

    Returns
    -------
    dict or None
        ``{"root": document_root}`` when a root is given, otherwise None.
    """
    return {"root": document_root} if document_root is not None else None


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


def _document_summary(document: Any) -> dict[str, Any]:
    """Summarize a parsed Document as a JSON-serializable object.

    Parameters
    ----------
    document : Any
        A Document returned by the documents service.

    Returns
    -------
    dict
        ``{"uri", "docType", "content"}`` with the content normalized for JSON.
    """
    return {
        "uri": document.uri,
        "docType": document.doc_type.value if document.doc_type else None,
        "content": _to_jsonable(document.content),
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
    except Exception:
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
    per_host = await asyncio.gather(
        *[_host_error_logs(service, params, host) for host in hosts],
    )
    return list(heapq.merge(*per_host, key=lambda entry: isoparse(entry["timestamp"])))


@mcp.tool(
    name="MLClientEnvs",
    annotations={"title": "List MarkLogic environments", **_READ_ONLY_HINTS},
)
async def ml_client_envs() -> str:
    """List mlclient environments discoverable from the working directory.

    Finds the nearest ``.mlclient`` directory (searching the server's working
    directory and its parents) and reports every ``mlclient-<name>.yaml``
    configuration in it. Call this first to learn which environment names the
    other tools accept.

    Returns
    -------
    str
        A JSON object, or an 'Error:' message when no .mlclient directory
        exists. On success:

        {
            "directory": str,          # Absolute path of the .mlclient directory
            "count": int,              # Number of environments found
            "environments": [
                {
                    "name": str,       # Environment name, e.g. "local"
                    "file": str        # Absolute path of its YAML file
                }
            ]
        }
    """
    try:
        directory = find_mlclient_directory(Path.cwd())
    except MLClientDirectoryNotFoundError as exc:
        return _error(exc)
    environments = [
        {"name": path.stem.removeprefix(_ENV_NAME_PREFIX), "file": str(path)}
        for path in sorted(directory.glob(_ENV_FILE_PATTERN))
    ]
    return json.dumps(
        {
            "directory": str(directory),
            "count": len(environments),
            "environments": environments,
        },
        indent=2,
    )


@mcp.tool(
    name="MLClientVersion",
    annotations={"title": "Read MarkLogic version", **_READ_ONLY_HINTS},
)
async def ml_client_version(params: EnvironmentInput) -> str:
    """Return the MarkLogic Server version for an environment.

    Parameters
    ----------
    params : EnvironmentInput
        Validated input containing:
            - environment (str): mlclient environment name

    Returns
    -------
    str
        A JSON object ``{"environment": str, "version": str}`` on success, or an
        'Error:' message describing a connection or configuration failure.
    """
    try:
        async with _connect(params.environment) as client:
            version = await client.version()
        return _dump({"environment": params.environment, "version": str(version)})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientHealth",
    annotations={"title": "Check MarkLogic health", **_READ_ONLY_HINTS},
)
async def ml_client_health(params: HealthInput) -> str:
    """Report whether the environment's MarkLogic health app server responds.

    By default this checks once. With ``wait`` it polls every
    ``interval_seconds`` and returns on the first healthy response, giving up
    after ``timeout_seconds``; this is the way to wait for a server that is
    still starting or restarting.

    Parameters
    ----------
    params : HealthInput
        Validated input containing:
            - environment (str): mlclient environment name
            - wait (bool): poll until healthy instead of a single check
            - interval_seconds (float): seconds between polls when wait=true
            - timeout_seconds (float): maximum total seconds to wait

    Returns
    -------
    str
        A JSON object on success, or an 'Error:' message describing a connection
        or configuration failure. A single check returns
        ``{"environment": str, "healthy": bool}``; a wait additionally returns
        ``"attempts"`` (int) and ``"timed_out"`` (bool).
    """
    try:
        async with _connect(params.environment) as client:
            if params.wait:
                result = await _wait_for_health(
                    client,
                    params.interval_seconds,
                    params.timeout_seconds,
                )
            else:
                result = {"healthy": await client.healthcheck()}
        return _dump({"environment": params.environment, **result})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientEval",
    annotations={
        "title": "Evaluate XQuery or JavaScript",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def ml_client_eval(params: EvalInput) -> str:
    """Evaluate XQuery or JavaScript on MarkLogic and return the parsed result.

    This runs arbitrary server-side code and can modify data; prefer a dedicated
    read tool for routine lookups. The result is parsed by mlclient and
    serialized to JSON.

    Parameters
    ----------
    params : EvalInput
        Validated input containing:
            - environment (str): mlclient environment name
            - code (str): XQuery or JavaScript source
            - language (EvalLanguage): 'xquery' (default) or 'javascript'
            - variables (Optional[dict]): external variables bound by name
            - database (Optional[str]): target database name

    Returns
    -------
    str
        The parsed result serialized as JSON (a scalar, object, string-rendered
        XML node, or a list of these), or an 'Error:' message describing a query
        or connection failure.
    """
    try:
        async with _connect(params.environment) as client:
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
        return _dump(result)
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientEstimate",
    annotations={"title": "Estimate matching fragment count", **_READ_ONLY_HINTS},
)
async def ml_client_estimate(params: EstimateInput) -> str:
    """Estimate how many fragments match a query, directly from indexes.

    This is an estimate from cts:estimate - a fast, index-only fragment count,
    not an exact document count. Use it to size a result set before searching.

    Parameters
    ----------
    params : EstimateInput
        Validated input containing:
            - environment (str): mlclient environment name
            - query (str): cts:query expression to count
            - document_root (str, optional): root element to scope to
            - database (str, optional): target database name

    Returns
    -------
    str
        A JSON object ``{"environment": str, "estimate": int}`` on success, or an
        'Error:' message describing a query or connection failure.
    """
    try:
        result = await _eval(
            params.environment,
            "cts:estimate(" + _scoped(params.query, params.document_root) + ")",
            variables=_root_vars(params.document_root),
            database=params.database,
        )
        return _dump({"environment": params.environment, "estimate": result})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientUris",
    annotations={"title": "List matching document URIs", **_READ_ONLY_HINTS},
)
async def ml_client_uris(params: UrisInput) -> str:
    """List the URIs of documents matching a query, with pagination.

    Returns only URIs, not document content; pair with MLClientDocs to fetch the
    documents themselves.

    Parameters
    ----------
    params : UrisInput
        Validated input containing:
            - environment (str): mlclient environment name
            - query (str): cts:query expression to match
            - document_root (str, optional): root element to scope to
            - start (int): 1-based index of the first URI
            - page_size (int): maximum number of URIs
            - database (str, optional): target database name

    Returns
    -------
    str
        A JSON object ``{"environment": str, "uris": [str]}`` on success, or an
        'Error:' message describing a query or connection failure.
    """
    try:
        result = await _eval(
            params.environment,
            "cts:search(fn:collection(), "
            + _scoped(params.query, params.document_root)
            + ', "unfiltered")'
            + _page_slice(params.start, params.page_size)
            + " ! xdmp:node-uri(.)",
            variables=_root_vars(params.document_root),
            database=params.database,
        )
        return _dump({"environment": params.environment, "uris": _as_list(result)})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientSearch",
    annotations={"title": "Search documents", **_READ_ONLY_HINTS},
)
async def ml_client_search(params: SearchInput) -> str:
    """Search documents matching a query and return a page plus the total.

    Each result carries the document URI and its serialized content. The total
    is an index estimate of all matches, independent of the returned page.

    Parameters
    ----------
    params : SearchInput
        Validated input containing:
            - environment (str): mlclient environment name
            - query (str): cts:query expression to match
            - document_root (str, optional): root element to scope to
            - start (int): 1-based index of the first result
            - page_size (int): maximum number of documents
            - database (str, optional): target database name

    Returns
    -------
    str
        A JSON object ``{"environment", "total", "start", "pageSize", "results"}``
        where each result is ``{"uri", "document"}``, or an 'Error:' message
        describing a query or connection failure.
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
            " cts:search(fn:collection(), " + scoped + ', "unfiltered")'
            + _page_slice(params.start, params.page_size)
            + ' ! object-node { "uri": xdmp:node-uri(.), "document": xdmp:quote(.) }'
            " }"
            "}",
            variables=_root_vars(params.document_root),
            database=params.database,
        )
        return _dump({"environment": params.environment, **result})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientValues",
    annotations={"title": "Read range-index values", **_READ_ONLY_HINTS},
)
async def ml_client_values(params: ValuesInput) -> str:
    """Read co-occurring values from a range index, by descending frequency.

    Reads the lexicon of a range index named by a cts:reference expression,
    optionally constrained to documents matching a query. Use it to discover the
    distinct values of a field, such as facet candidates.

    Parameters
    ----------
    params : ValuesInput
        Validated input containing:
            - environment (str): mlclient environment name
            - reference (str): cts:reference expression naming the range index
            - query (str): cts:query expression constraining contributing docs
            - limit (int): maximum number of values
            - database (str, optional): target database name

    Returns
    -------
    str
        A JSON object ``{"environment": str, "values": [...]}`` on success, or an
        'Error:' message describing a query or connection failure.
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
        )
        return _dump({"environment": params.environment, "values": _as_list(result)})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientDocs",
    annotations={"title": "Read documents by URI", **_READ_ONLY_HINTS},
)
async def ml_client_docs(params: DocsInput) -> str:
    """Read one or more documents by URI and return their content.

    Parameters
    ----------
    params : DocsInput
        Validated input containing:
            - environment (str): mlclient environment name
            - uris (list[str]): document URIs to read
            - category (list[str], optional): content categories to read
            - database (str, optional): target database name

    Returns
    -------
    str
        A JSON object ``{"environment": str, "documents": [...]}`` where each
        document is ``{"uri", "docType", "content"}``, or an 'Error:' message
        describing a read or connection failure.
    """
    try:
        async with _connect(params.environment) as client:
            documents = await client.documents.read(
                params.uris,
                category=params.category,
                database=params.database,
            )
        found = documents.values() if isinstance(documents, dict) else [documents]
        return _dump(
            {
                "environment": params.environment,
                "documents": [_document_summary(document) for document in found],
            },
        )
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientLogs",
    annotations={"title": "Read server logs", **_READ_ONLY_HINTS},
)
async def ml_client_logs(params: LogsInput) -> str:
    """Read a MarkLogic server's logs, optionally filtered by time and regex.

    Time and regex filters apply to error logs only; they are ignored for other
    log kinds.

    Set ``all_hosts`` to aggregate error logs from every cluster host, merged by
    timestamp and tagged with their host; it supports the error log type only and
    cannot be combined with ``host``.

    Parameters
    ----------
    params : LogsInput
        Validated input containing:
            - environment (str): mlclient environment name
            - app_server (str, optional): app server port whose logs to read
            - log_type (LogKind): 'error' (default), 'access', 'request', 'audit'
            - start_time, end_time (str, optional): ISO 8601 bounds, error logs
            - regex (str, optional): line filter, error logs
            - host (str, optional): host whose logs to read
            - all_hosts (bool): aggregate error logs across every cluster host

    Returns
    -------
    str
        A JSON object ``{"environment": str, "logs": [...]}`` on success, or an
        'Error:' message describing a connection, validation or retrieval failure.
    """
    if params.all_hosts and (
        params.host is not None or params.log_type is not LogKind.ERROR
    ):
        return (
            "Error: all_hosts supports the error log type only and cannot be "
            "combined with host."
        )
    try:
        async with _connect(params.environment) as client:
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
        return _dump({"environment": params.environment, "logs": logs})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="MLClientIndexes",
    annotations={"title": "List database range indexes", **_READ_ONLY_HINTS},
)
async def ml_client_indexes(params: DatabaseInput) -> str:
    """List the range indexes configured on a database.

    Returns the element, element-attribute, path and field range index
    definitions from the database properties. Use it to find which fields are
    available for range queries, sorting and lexicon reads.

    Parameters
    ----------
    params : DatabaseInput
        Validated input containing:
            - environment (str): mlclient environment name
            - database (str): database name to inspect

    Returns
    -------
    str
        A JSON object ``{"environment", "database", "indexes"}`` on success, or an
        'Error:' message describing a connection or management failure.
    """
    try:
        async with _connect(params.environment) as client:
            response = await client.manage.databases.get_properties(
                params.database,
                data_format="json",
            )
        MLResponseParser.raise_for_status(response)
        properties = response.json()
        return _dump(
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
        return _error(exc)


@mcp.tool(
    name="MLClientDbStatus",
    annotations={"title": "Read database status", **_READ_ONLY_HINTS},
)
async def ml_client_db_status(params: DatabaseInput) -> str:
    """Report a database's runtime status from the Management API.

    Parameters
    ----------
    params : DatabaseInput
        Validated input containing:
            - environment (str): mlclient environment name
            - database (str): database name to inspect

    Returns
    -------
    str
        A JSON object ``{"environment", "database", "status"}`` on success, or an
        'Error:' message describing a connection or management failure.
    """
    try:
        async with _connect(params.environment) as client:
            response = await client.manage.databases.get(
                params.database,
                view="status",
                data_format="json",
            )
        MLResponseParser.raise_for_status(response)
        return _dump(
            {
                "environment": params.environment,
                "database": params.database,
                "status": response.json(),
            },
        )
    except Exception as exc:
        return _error(exc)


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
async def ml_client_http(params: HttpInput) -> str:
    """Send a raw HTTP request to the environment's primary app server.

    This is the generic fallback for endpoints without a dedicated tool. It can
    modify data depending on method and endpoint, so prefer a dedicated read tool
    when one exists. Requests target the primary REST app server connection.

    Parameters
    ----------
    params : HttpInput
        Validated input containing:
            - environment (str): mlclient environment name
            - method (HttpMethod): GET (default), POST, PUT, DELETE or HEAD
            - endpoint (str): request path on the primary app server
            - params (dict, optional): query-string parameters
            - body (str or dict, optional): request body; a dict is sent as JSON
            - headers (dict, optional): request headers

    Returns
    -------
    str
        A JSON object ``{"environment", "status", "body"}`` where body is parsed
        JSON when possible else text, or an 'Error:' message describing a request
        or connection failure.
    """
    try:
        async with _connect(params.environment) as client:
            response = await client.http.request(
                params.method.value,
                params.endpoint,
                body=params.body,
                params=params.params,
                headers=params.headers,
            )
        return _dump(
            {
                "environment": params.environment,
                "status": response.status_code,
                "body": _response_body(response),
            },
        )
    except Exception as exc:
        return _error(exc)


def main() -> None:
    """Run the MCP server over stdio transport."""
    mcp.run()
