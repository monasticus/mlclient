# MCP server

Use MLClient from an MCP client to inspect MarkLogic environments, search content,
read documents and logs, or evaluate XQuery and JavaScript. The server uses your
existing MLClient environment files and runs locally over stdio.

## Install and connect

Install the optional MCP dependency in the Python environment that will run the
server:

```sh
pip install 'mlclient[mcp]'
```

For development from this repository, use `poetry install --extras mcp`.
The Python library and `ml` CLI can still be installed without the MCP extra.

Create an environment in your project if you do not already have one:

```sh
cd /path/to/project
ml env init local
python -m mlclient.mcp
```

The last command waits for MCP messages; it is not an interactive shell.
Configure your MCP client to start it in the project directory. For clients that
accept a `mcpServers` JSON configuration, the entry looks like this:

```json
{
  "mcpServers": {
    "mlclient": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["-m", "mlclient.mcp"],
      "cwd": "/path/to/project"
    }
  }
}
```

Use the configuration format supported by your client. If it cannot set `cwd`,
launch Python from a small wrapper that changes into your project first.
MLClient searches for the nearest `.mlclient` directory from the server's working
directory upward. It does not search from the MCP client's conversation or file.
Credentials stay in the environment configuration; tool calls contain names, not
passwords. Do not commit files containing credentials.

## Choose an environment and connection

Call `MLClientEnvs` with `{}` to discover environment names and configuration paths.
Other tools receive their fields inside a `params` object:

```json
{"params": {"environment": "local"}}
```

`environment: "local"` loads `.mlclient/mlclient-local.yaml`.
Use `connection` to select a configured app-server identifier when the environment
has several connections. Content, Eval, Version and Http tools default to the
first REST connection. Health defaults to `health`; Logs, Indexes and DbStatus
default to `manage`, so these tools do not require a configured REST connection.
For content tools, `database` optionally overrides the selected REST server's
content database. It does not choose a different HTTP connection.

## Tools

| Tool | Purpose |
| --- | --- |
| `MLClientEnvs` | Discover locally configured environments. |
| `MLClientVersion` | Read the server version. |
| `MLClientHealth` | Check health, or wait up to a deadline with `wait: true`. |
| `MLClientEstimate` | Estimate matching fragments using a CTS query. |
| `MLClientUris` | List a page of document URIs matching a CTS query. |
| `MLClientSearch` | Return a page of matching documents and an estimated total. |
| `MLClientValues` | Read distinct range-index values in descending frequency order. |
| `MLClientDocs` | Read documents by URI, including requested metadata. |
| `MLClientLogs` | Read the latest filtered log entries, optionally across hosts. |
| `MLClientIndexes` | Inspect range-index definitions. |
| `MLClientDbStatus` | Inspect database runtime status. |
| `MLClientEval` | Run XQuery or JavaScript. |
| `MLClientHttp` | Send a request to an endpoint on the selected connection. |

### Search and read

Start with a count or URI page before downloading content:

```json
{
  "params": {
    "environment": "local",
    "query": "cts:collection-query(\"orders\")",
    "start": 1,
    "page_size": 10
  }
}
```

Pass this to `MLClientUris` or `MLClientSearch`. Search results are filtered;
`total` remains an index estimate of fragments, not an exact document count.
Pagination starts at 1. URI pages default to 100 and allow up to 1000 entries;
Search pages default to 10 and allow up to 100 documents.

To scope an XML query to a root element, supply `document_root` as its local name.
`root_namespace` is the namespace URI; omit it for roots without a namespace.

Read the selected documents with `MLClientDocs`:

```json
{
  "params": {
    "environment": "local",
    "uris": ["/orders/one.json"],
    "category": ["content", "metadata"],
    "max_chars": 20000
  }
}
```

A call accepts up to 100 URIs. Each document includes `uri`, `docType`, `content`,
`metadata` and `truncated`. Content exceeding `max_chars` is returned as a text
preview marked `truncated: true`; it is not a complete document or valid JSON/XML
for writing back. The default is 20000 characters per document; the maximum is
100000. Request fewer documents or increase the limit when a preview is too short.

### Logs and health

Read the latest error logs with `MLClientLogs`:

```json
{
  "params": {
    "environment": "local",
    "all_hosts": true,
    "start_time": "2026-10-05T08:00:00Z",
    "regex": "Error|Warning",
    "limit": 100
  }
}
```

Time and regex filters apply to error logs. `all_hosts` supports error logs only
and cannot be combined with `host`. The result reports `total` fetched entries and
`truncated`, and returns the latest `limit` entries in timestamp order for error
logs. The default limit is 100; the maximum is 1000. The limit bounds returned
output, not the server log download; use time filters to reduce retrieval work.

`MLClientHealth` checks once by default. With `wait: true`, it retries temporary
transport failures until healthy or until `timeout_seconds` expires (default 120,
maximum 600). Waiting returns `attempts` and `timed_out` as well as `healthy`.
The deadline includes time spent in health requests. A health timeout is a normal
unhealthy result; invalid configuration or HTTP 4xx errors are tool errors.

### Eval and raw HTTP

For `MLClientEval`, supply `code`, optionally `language: "javascript"`, `variables`
and `database`. XQuery external variables must be declared in the supplied code.
The result object contains `environment` and `result`.

For `MLClientHttp`, supply `method`, an absolute `endpoint` path, and optionally
`params`, `headers` and `body`. A dictionary body defaults to JSON; an explicit `Content-Type` header overrides
that default. Use
`connection: "manage"` explicitly for a Manage API request. Absolute URLs and
fragments are rejected. The result contains `status` and a JSON or text `body`;
HTTP 4xx/5xx responses remain inspectable through that status field.

## Results, errors and privileges

Tools return structured JSON objects, also available as text for clients that
only display text. XML is serialized as a string. Binary values are losslessly
represented as `{"encoding": "base64", "data": "..."}`. Decimal and date/time
values are strings. Results over 200000 serialized characters fail with an
instruction to request a smaller result rather than silently omitting data.
Execution and configuration failures use MCP tool errors (`isError: true`), with
suggested next steps for missing environments.

**Query and reference fields are XQuery code.** Estimate, Uris, Search and Values
accept arbitrary expressions, just as Eval accepts arbitrary code. They are
marked as potentially destructive and non-idempotent: the MCP server does not
sandbox those expressions or enforce read-only execution. Http can also modify
data. Use account privileges and your client's approval policy to control access;
for inspection-only use, configure a suitably restricted MarkLogic account.

Eval-based tools require the server's REST eval privileges; selecting another
database also requires permission to evaluate in it. Documents require access to
the requested documents, and management tools require their respective Manage
API privileges. Values additionally requires the referenced range index.
A dedicated read tool is easier to use but is not a substitute for access control.

See [environments](environments.md), [authentication](python/connections.md), and
the [MCP Python reference](../reference/mlclient/mcp/index.md).
