# Python guide

Start with [the quickstart](../quickstart.md) to connect and evaluate a query.
Use a context manager so connections close even when an operation fails.
Choose `MLClient` for synchronous scripts or `AsyncMLClient` inside async code.

## Choose how much control you need

The same client exposes three levels. Use the highest level that fits the task;
you can combine them in one application.

| Entry point | Result | Use it for |
| --- | --- | --- |
| `ml.documents`, `ml.eval`, `ml.logs` | Parsed Python values and document models | Application work without handling HTTP payloads yourself |
| `ml.rest`, `ml.manage`, `ml.admin` | HTTPX responses from resource methods | Explicit MarkLogic REST operations and response handling |
| `ml.http` | HTTPX responses from arbitrary requests | Endpoints without a wrapper and custom application routes |

```python
from mlclient import MLClient

with MLClient() as ml:  # Local development defaults; configure your credentials.
    document = ml.documents.read("/example.json")
    response = ml.rest.documents.get(uri="/example.json")
    raw_response = ml.http.get("/v1/documents", params={"uri": "/example.json"})
```

These are three alternative ways to read the same existing document, not three
steps required for a read. Raw requests use the primary connection; their paths
do not automatically select Manage or Admin ports.

## Pick a task

- [Documents](python/documents.md): content types, metadata, reading, writing and deletion.
- [Evaluate code](python/eval.md): XQuery, JavaScript and external variables.
- [Transactions](python/transactions.md): commit or roll back related operations.
- [Read logs](python/logs.md): parsed server logs for scripts.
- [Health, versions and administration](python/operations.md): inspect the server and change log levels.

## Configure and extend

For credentials, TLS, Cloud and authentication choices, read
[Connection and authentication](python/connections.md). For project configuration,
manager factories, timeout, retry and pool limits, read
[Environments and runtime settings](setup.md).

[API layers](python/api-layers.md) explains the lower-level interfaces.
[Custom application APIs](python/custom-api.md) builds an endpoint wrapper and
adds it to your own client without touching MLClient internals.

The [API reference](../reference/mlclient/index.md) contains complete signatures
and docstrings. The `mlclient.jobs` package remains experimental; use document
services for operations covered by the [stability contract](../stability.md).
