# Services

The API tiers - `ml.rest`, `ml.manage`, `ml.admin` and `ml.http` - speak HTTP.
You pass endpoint parameters and get back an httpx `Response`: a status code,
headers and a body you read and interpret yourself.

Services sit one level above. A service calls those tiers internally, then does
the work you would otherwise repeat by hand - it applies sensible defaults,
sends the request, checks the status, and parses the body into a Python value: a
document model, a `dict`, a `datetime`. You work with results, not payloads.

Reach for a service whenever one covers what you need. Drop to an API tier only
for an endpoint no service wraps, or when you need the raw status and headers.
See [Clients](../clients.md) for the full tier map.

## Client services

The essential services hang off a connected client, ready to use:

| Service | Access | Guide |
| --- | --- | --- |
| Documents | `ml.documents` | [Documents](documents.md) |
| Evaluate code | `ml.eval` | [Evaluate code](eval.md) |
| Transactions | `ml.transaction()` | [Transactions](transactions.md) |

```python
from mlclient import MLClient

with MLClient() as ml:
    document = ml.documents.read("/example.json")
    result = ml.eval.xquery("1 + 1")
```

`ml.documents` and `ml.eval` are properties returning stateless services.
`ml.transaction()` is a method instead: opening a transaction performs a
request, so it returns a
[TransactionService][mlclient.services.TransactionService] scoped
to that transaction - a
context manager that commits on a clean exit, rolls back on error, and unpacks
with `**` into the operations it should cover. See
[Transactions](transactions.md).

## Additional services

Other services are not on the client facade. They cover narrower or more
operational needs, so instead of a ready property you construct them yourself
and pass the API tier handle they build on. They are the same layer - parsed
Python output, defaults applied - just off the curated client surface.

### Logs

[LogsService][mlclient.services.LogsService] returns parsed log records
through the Management API. Construct it from `ml.manage`:

```python
from mlclient import MLClient
from mlclient.services import LogsService

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

### Log level

[LogLevelService][mlclient.services.LogLevelService] reads or changes
a group or App Server log level. It evaluates
the Admin module through the REST server first and falls back to the Management
API only when the connecting user lacks the eval privilege - so it needs both
`ml.rest` and `ml.manage`:

```python
from mlclient import MLClient
from mlclient.services import LogLevelService

with MLClient() as ml:
    levels = LogLevelService(ml.rest, ml.manage)
    current = levels.get(group="Default", log_type="file")
    levels.set(current, group="Default", log_type="file")
```

Omit `server` to target a group, or supply an App Server name for its file log
level; App Servers have no system log level. Both `get` and `set` accept a
keyword-only `timeout`. Use the [log-level command](../cli/log-level.md) for
supported levels and the Management permissions each path needs.

### Trace events

[TraceEventsService][mlclient.services.TraceEventsService] reads and changes
group diagnostics through the REST server's Admin-module evaluation:

```python
from mlclient import MLClient
from mlclient.services import TraceEventsService

with MLClient() as ml:
    traces = TraceEventsService(ml.rest)
    state = traces.get(group="Default")
    print(state.activated, state.events)
```

The immutable [TraceEvents][mlclient.services.TraceEvents] result contains the
master `activated` flag and an alphabetically sorted tuple of configured event
names. `set_event("XDMP Deadlock", enabled=True)` adds an event without changing
activation; `set_activated(value=True)` changes the master switch without changing
event membership. Both return the state read after saving. Repeated additions and
removals are idempotent.

This service is synchronous and needs only `ml.rest`; it does not fall back to
Manage. All three operations accept keyword-only `group` and `timeout`. A timeout
override applies independently to the mutation and follow-up read, not to their
total duration. Omitting it inherits the client timeout; `None` disables it.

Recognized server errors raise `MarkLogicError`; other HTTP failures raise
`httpx.HTTPStatusError`, and transport errors propagate. A failed read-back does
not roll back a successful save. See [trace-events](../cli/trace-events.md) for
permissions and the corresponding CLI workflow.

## Building your own

To wrap an endpoint no service covers, see
[Custom application APIs](custom-api.md), which adds an endpoint wrapper to your
own client without touching MLClient internals.
