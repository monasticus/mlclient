# Services

The API tiers - `ml.rest`, `ml.manage`, `ml.admin` and `ml.http` - speak HTTP.
You pass endpoint parameters and get back an [`httpx.Response`](https://www.python-httpx.org/api/#response): a status code,
headers and a body you read and interpret yourself.

Services sit one level above. A service calls those tiers internally, then does
the work you would otherwise repeat by hand - it applies sensible defaults,
sends the request, checks the status, and parses the body into a Python value: a
document model, a `dict`, a `datetime`. You work with results, not payloads.

Reach for a service whenever one covers what you need. Drop to an API tier only
for an endpoint no service wraps, or when you need the raw status and headers.
See [Clients](../guides/clients.md) for the full tier map.

## Client services

Documents, evaluation, module invocation, search and transactions are available directly on the
client:

| Service | Access | Guide |
| --- | --- | --- |
| Documents | `ml.documents` | [Documents](../guides/documents.md) |
| Evaluate code | `ml.eval` | [Evaluate code](../guides/eval.md) |
| Invoke modules | `ml.invoke` | [Invoke modules](../guides/invoke.md) |
| Search | `ml.search` | [Search](../guides/search.md) |
| Transactions | `ml.transaction()` | [Transactions](../guides/transactions.md) |

```python
from mlclient import MLClient

with MLClient() as ml:
    document = ml.documents.read("/example.json")
    result = ml.eval.xquery("1 + 1")
```

### Reuse a scoped service

`ml.documents`, `ml.eval`, `ml.invoke` and `ml.search` start with an empty scope. Calling one
with settings, such as `ml.documents(database="catalog")`, returns a new service
that uses those defaults for subsequent operations. Creating it sends no request
and leaves the original service unchanged; both share the same connection.

| Service | Empty scope | With defaults | Scope type |
| --- | --- | --- | --- |
| Documents | `ml.documents` | `ml.documents(database="catalog")` | [ServiceScope][mlclient.services.ServiceScope] |
| Evaluation | `ml.eval` | `ml.eval(database="catalog")` | [ServiceScope][mlclient.services.ServiceScope] |
| Invocation | `ml.invoke` | `ml.invoke(database="catalog")` | [ServiceScope][mlclient.services.ServiceScope] |
| Search | `ml.search` | `ml.search(database="catalog", collection="products")` | [SearchScope][mlclient.services.SearchScope] |

`ServiceScope` holds `database` and `txid`. `SearchScope` also supports search
settings, such as collections, directories and query options:

```python
with MLClient() as ml:
    documents = ml.documents(database="catalog")
    evaluation = ml.eval(database="catalog")
    products = ml.search(database="catalog", collection="products")

    document = documents.read("/example.json")
    result = evaluation.xquery("1 + 1")
    uris = products.uris("coffee")
```

On all four services, per-operation `database=` and `txid=` arguments override
the service defaults; `None` clears an inherited value. Transaction settings can
also be unpacked with `**txn`, on the service (`ml.documents(**txn)`) or an
operation (`ml.documents.read("/example.json", **txn)`). For search-specific
per-operation settings, use `scope=SearchScope(...)`. See
[Search scope](../guides/search.md#scope-databases-filters-and-options).

### Open a transaction

`ml.transaction()` is a method instead: opening a transaction performs a
request, so it returns a
[TransactionService][mlclient.services.TransactionService] scoped
to that transaction - a
context manager that commits on a clean exit, rolls back on error, and unpacks
with `**` into the operations it should cover, such as
`ml.search.uris(**txn)`. See [Transactions](../guides/transactions.md).

## Additional services

Construct these services from the API tier handles on an existing client. They
use the same connections and return parsed Python results, but are not properties
on the client facade.

### CTS search

[CtsService][mlclient.services.CtsService] executes CTS queries through eval.
Use it to search XML subtrees or combine search with other XQuery operations:

```python
from mlclient.services import CtsService
from mlclient.xquery import cts

with MLClient() as ml:
    search = CtsService(ml.rest)
    hits = search.search(query=cts.collection_query("products"), pos=[1, 10])
```

It needs eval privileges. For ordinary REST searches with structured, CTS or
text queries, use `ml.search`. See
[CTS search with eval](../guides/search.md#cts-search-with-eval) for query composition
and the async counterpart.

### Diagnostics

Operational services live in
[mlclient.services.diagnostics][mlclient.services.diagnostics]. They read logs,
change log levels and manage trace events.

#### Logs

[LogsService][mlclient.services.diagnostics.LogsService] returns parsed log records
through the Management API. Construct it from `ml.manage`:

```python
from mlclient import MLClient
from mlclient.services.diagnostics import LogsService

with MLClient() as ml:
    logs = LogsService(ml.manage)
    for record in logs.get(8002, "error"):
        print(record)
    files = logs.list()
```

The Management connection uses its own configuration, normally port 8002. `get`
filters by app server, log type, time range and regex; `list` returns the
available log files. Prefer a time range over refetching a whole file for large
logs. Use the [logs command](../cli/logs.md) when you only need terminal output.

#### Log level

[LogLevelService][mlclient.services.diagnostics.LogLevelService] reads or changes
a group or App Server log level. It evaluates
the Admin module through the REST server first and falls back to the Management
API only when the connecting user lacks the eval privilege - so it needs both
`ml.rest` and `ml.manage`:

```python
from mlclient import MLClient
from mlclient.services.diagnostics import LogLevelService

with MLClient() as ml:
    levels = LogLevelService(ml.rest, ml.manage)
    current = levels.get(group="Default", log_type="file")
    levels.set(current, group="Default", log_type="file")
```

Omit `server` to target a group, or supply an App Server name for its file log
level; App Servers have no system log level. Both `get` and `set` accept a
keyword-only `timeout`. Use the [log-level command](../cli/log-level.md) for
supported levels and the Management permissions each path needs.

#### Trace events

[TraceEventsService][mlclient.services.diagnostics.TraceEventsService] reads and changes
group diagnostics through the REST server's Admin-module evaluation:

```python
from mlclient import MLClient
from mlclient.services.diagnostics import TraceEventsService

with MLClient() as ml:
    traces = TraceEventsService(ml.rest)
    state = traces.get(group="Default")
    print(state.activated, state.events)
```

The immutable [TraceEvents][mlclient.services.diagnostics.TraceEvents] result contains the
master `activated` flag and an alphabetically sorted tuple of configured event
names. `set_event("XDMP Deadlock", enabled=True)` adds an event without changing
activation; `set_activated(value=True)` changes the master switch without changing
event membership. Both return the state read after saving. Repeated additions and
removals are idempotent.

This service is synchronous and needs only `ml.rest`; it does not fall back to
Manage. All three operations accept keyword-only `group` and `timeout`. A timeout
override applies independently to the mutation and follow-up read, not to their
total duration. Omitting it inherits the client timeout; `None` disables it.

Recognized server errors raise [`MarkLogicError`][mlclient.exceptions.MarkLogicError]; other HTTP failures raise
[`httpx.HTTPStatusError`](https://www.python-httpx.org/exceptions/#exception-classes:~:text=class%20httpx.HTTPStatusError), and transport errors propagate. A failed read-back does
not roll back a successful save. See [trace-events](../cli/trace-events.md) for
permissions and the corresponding CLI workflow.

## Building your own

To wrap an endpoint no service covers, see
[Custom application APIs](custom-api.md), which adds an endpoint wrapper to your
own client without touching MLClient internals.
