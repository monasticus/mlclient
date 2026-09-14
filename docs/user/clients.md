# Clients

Start with [the quickstart](../quickstart.md) to connect and evaluate a query.
Use a context manager so connections close even when an operation fails.
Choose `MLClient` for synchronous scripts or `AsyncMLClient` inside async code.
These clients are facades combining services and several APIs. You can also
[use a single API directly](#use-one-api-without-the-facade).

## Imports

Import the main clients from `mlclient`:

```python
from mlclient import MLClient, AsyncMLClient
```

Additional types are grouped by purpose:

| Module | Examples |
| --- | --- |
| `mlclient.env` | `MLEnvironment`, `MLServerConfig` |
| `mlclient.http` | `HTTPConfig`, `UNSET`, retry and timeout defaults |
| `mlclient.auth` | `AuthConfig`, `OAuthBearerAuth` |
| `mlclient.connection` | `SSLConfig`, `CloudConfig` |
| `mlclient.models` | `Document`, `Metadata`, `Category`, `MarkLogicVersion` |
| `mlclient.clients` | `HttpClient`, `ApiClient` and their async counterparts |
| `mlclient.api` | `RestApi`, `DocumentsApi` and other endpoint wrappers |
| `mlclient.calls` | `ApiCall`, `EvalCall` and other request objects |
| `mlclient.services` | `DocumentsService`, `TransactionService` |
| `mlclient.responses` | `MLResponseParser` |
| `mlclient.io` | `DocumentsLoader`, `DocumentsWriter` |
| `mlclient.exceptions` | `MarkLogicError`, `ConfigError` |

The [API reference](../reference/mlclient/index.md) shows the import for every
public class and function. Modules starting with `_` contain internal code.
Use `httpx.Timeout`, `httpx.Limits`, and `httpx_retries.Retry` directly when
customizing the corresponding HTTP settings.

## Entry points at a glance

Each entry point differs on two independent axes: how much it parses for you,
and which MarkLogic server it targets. The two sections after this table explain
each axis.

| Entry point               | Returns                    | Server (port)       | Reach for it when |
| ------------------------- | -------------------------- | ------------------- | ----------------- |
| `ml.documents`, `ml.eval` | Parsed values and models   | REST (main)         | You want Python values without handling HTTP yourself |
| `ml.transaction()`        | Transaction context manager | REST (main)        | You group operations to commit or roll back together |
| `ml.rest`                 | `httpx.Response`           | REST (main)         | Named `/v1/*` operations where you read the response |
| `ml.manage`               | `httpx.Response`           | Manage (8002)       | Management API (`/manage/v2/*`) operations |
| `ml.admin`                | `httpx.Response`           | Admin (8001)        | Admin API (`/admin/v1/*`) operations |
| `ml.http`                 | `httpx.Response`           | Main port, any path | An endpoint without a wrapper, or a custom route |
| `ml.parser`               | Parses a `httpx.Response`  | -                   | You have a response and want the value a service would give |

`ml.transaction()` is a method, not a property: opening a transaction performs a
request, so it returns a service scoped to that transaction rather than a shared
one. See [Transactions](#transactions).

## Abstraction: parsed, response, or raw

The client works at three levels of abstraction. Use the highest one that fits
the task; you can mix them in one application.

- **Services** (`ml.documents`, `ml.eval`) parse the response into Python values
  and document models.
- **Wrappers** (`ml.rest`, `ml.manage`, `ml.admin`) build the request for a named
  endpoint and return the raw `httpx.Response`.
- **Raw HTTP** (`ml.http`) sends an arbitrary request on the primary connection.

The three read the same document three different ways:

```python
from mlclient import MLClient

with MLClient() as ml:  # Local development defaults; configure your credentials.
    document = ml.documents.read("/example.json")
    rest_response = ml.rest.documents.get(uri="/example.json")
    http_response = ml.http.get("/v1/documents", params={"uri": "/example.json"})
```

`rest_response` and `http_response` are both `httpx.Response` objects, each
from a separate request. The wrapper builds the request for you. Only `ml.documents.read` parses the body into a
model. Reach for a service by default, drop to a wrapper or `ml.http` when you
need the raw response, and [parse it back](#parse-a-response) when you want the
parsed value without the service.

## Server tiers and ports

Each API targets a server connection. MLClient uses these ports by default:

| Tier              | Port        | Endpoints      |
|-------------------|-------------|----------------|
| Client (REST) API | 8000/custom | `/v1/*`        |
| Admin API         | 8001        | `/admin/v1/*`  |
| Management API    | 8002        | `/manage/v2/*` |

Port 8000 is the default App-Services REST server. A custom REST App Server
uses its configured port.

`ml.rest` uses the primary connection. By default, `.manage` uses port 8002
and `.admin` uses port 8001, inheriting the primary connection settings except
for the port. Changing the primary port leaves these auxiliary defaults intact:

```python
>>> from mlclient import MLClient

# Default port 8000 - .manage uses 8002, .admin uses 8001
>>> with MLClient() as ml:
...     resp = ml.manage.databases.get_list()
...     ts = ml.admin.get_timestamp()

# Custom REST server on port 8040 - .rest uses 8040, .manage/.admin still 8002/8001
>>> with MLClient(port=8040) as ml:
...     resp = ml.rest.eval.post(xquery="1")
...     dbs = ml.manage.databases.get_list()
```

`ml.http` is the exception: it sends on the primary connection and the path does
not select a port, so target Manage or Admin by connecting to their port.

For session lifecycle and overriding Manage or Admin connection settings, see [Connection and authentication](python/connections.md).

## Call a wrapper (REST, Manage, Admin)

Each wrapper exposes a named method per endpoint and returns an `httpx.Response`,
so you read status codes, headers and bodies yourself. Methods take endpoint
parameters as keyword arguments; the
[API reference](../reference/mlclient/index.md) lists each resource's signature.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     query = ml.rest.eval.post(xquery="xdmp:database-name(xdmp:database())")
...     databases = ml.manage.databases.get_list()
...     timestamp = ml.admin.get_timestamp()
```

## Use one API without the facade

The individual layers can be used independently. If you only need Admin
operations, compose [AdminApi][mlclient.api.AdminApi] with an
[ApiClient][mlclient.clients.ApiClient] and a
[HttpClient][mlclient.clients.HttpClient]:

```python
from mlclient.api import AdminApi
from mlclient.clients import ApiClient, HttpClient

with HttpClient(port=8001) as http:
    admin = AdminApi(ApiClient(http))
    response = admin.get_timestamp()
    print(response.text)
```

`HttpClient` owns the connection; its context manager closes it. The API wrappers
use that connection and do not select a port or create additional clients.
`RestApi` and `ManageApi` compose in the same way, using their respective server
configurations. Async code uses `AsyncHttpClient`, `AsyncApiClient` and the
corresponding async wrapper, with `async with` and awaited operations.

## Send a raw request (`ml.http`)

`ml.http` sends arbitrary requests on the primary connection. Strings and bytes
are sent as raw content; a `dict` is JSON-encoded for a JSON content type and
submitted as form data otherwise. Header names are case-insensitive.

```python
>>> from mlclient import MLClient

# GET with parameters and headers
>>> with MLClient(port=8002) as ml:
...     servers = ml.http.get(
...         "/manage/v2/servers",
...         params={"format": "json"},
...         headers={"custom-header": "custom-value"},
...     )

# POST a body
>>> with MLClient() as ml:
...     result = ml.http.post(
...         "/v1/eval",
...         {"xquery": "fn:current-dateTime()"},
...         params={"database": "Documents"},
...         headers={"Content-Type": "application/x-www-form-urlencoded"},
...     )
```

`ml.http` also has `put`, `delete` and a general `request` method with the same
body handling.

## Transactions

Group several operations so they commit or roll back together.
`ml.transaction()` returns a context manager that commits on a clean exit and
rolls back if the block raises; spread it with `**` into each operation to run
that operation inside the transaction:

```python
>>> from mlclient import MLClient
>>> from mlclient.models import Document

>>> doc = Document.create("/doc-1.xml", "<root>data</root>")
>>> with MLClient() as ml:
...     with ml.transaction() as txn:
...         ml.documents.write(doc, **txn)
...         ml.eval.xquery('xdmp:document-insert("/doc-2.xml", <root/>)', **txn)
```

See the [transactions guide](python/transactions.md) for rollback, reading the
id and status, manual commit, and what `**txn` unpacks to.

To drive the lifecycle through the raw wrapper instead, `ml.rest.transactions`
gives full control - create it, take the id from the `Location` header, thread
it through each call, then commit or roll back:

```python
>>> with MLClient() as ml:
...     location = ml.rest.transactions.create().headers["Location"]
...     txid = location.rsplit("/", 1)[-1]
...     try:
...         ml.documents.write(doc, txid=txid)
...         ml.rest.transactions.post(txid, result="commit")
...     except Exception:
...         ml.rest.transactions.post(txid, result="rollback")
...         raise
```

## Parse a response

Any wrapper or `ml.http` returns an `httpx.Response`. To get the parsed Python
value a service would give - a `dict` for JSON, a `datetime` for `xs:dateTime`,
and so on - hand it to `ml.parser`:

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     resp = ml.rest.eval.post(
...         xquery="xdmp:database() => xdmp:database-name()",
...     )
...     parsed = ml.parser.parse(resp)
>>> parsed
'Documents'
```

## Pick a task

- [Documents](python/documents.md): content types, metadata, reading, writing and deletion.
- [Evaluate code](python/eval.md): XQuery, JavaScript and external variables.
- [Transactions](python/transactions.md): commit or roll back related operations.
- [Services](python/services.md): the parsed higher-level layer, and the off-facade logs and log-level services.
- [Health, versions and administration](python/health-and-administration.md): inspect the server, versions and restart waits.

## Configure and extend

For credentials, TLS, Cloud and authentication choices, read
[Connection and authentication](python/connections.md). For project configuration,
and manager factories, read [Environments](environments.md). For transport options, start with
[HTTP configuration](http-configuration.md), then [timeouts](python/timeouts.md),
[retries](python/retries.md) or [resource limits](python/limits.md).

[Custom application APIs](python/custom-api.md) builds an endpoint wrapper and
adds it to your own client without touching MLClient internals.

The [API reference](../reference/mlclient/index.md) contains complete signatures
and docstrings. The `mlclient.jobs` package remains experimental; use document
services for operations covered by the [stability contract](../stability.md).
