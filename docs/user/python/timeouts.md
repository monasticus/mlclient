# Timeouts

Set a timeout when creating a client:

```python
from mlclient import MLClient

with MLClient(timeout=10) as ml:
    result = ml.eval.xquery('"Hello World!"')
```

A number sets all four HTTP timeout components to that many seconds. Use
`httpx.Timeout` to configure them independently:

```python
import httpx
from mlclient import MLClient

timeout = httpx.Timeout(connect=5, read=120, write=60, pool=5)
with MLClient(timeout=timeout) as ml:
    result = ml.eval.xquery('"Hello World!"')
```

## Timeout components

| Component | Limits time spent |
| --- | --- |
| `connect` | Opening a connection |
| `read` | Waiting between response chunks |
| `write` | Waiting between request-body chunks |
| `pool` | Waiting for a connection from the pool |

Read and write limits apply between chunks, not to the entire body.

## Override one request

Pass `timeout` to an operation to change it for that request only:

```python
with MLClient(timeout=10) as ml:
    ml.eval.xquery('"Hello World!"', timeout=2)
    ml.documents.read("/doc.xml", timeout=None)
    ml.healthcheck(timeout=2)
```

`None` disables all HTTP timeouts. Omitting the parameter inherits the client
setting. An override does not change later calls.

## Defaults

| Connection | Connect | Read | Write | Pool |
| --- | --- | --- | --- | --- |
| REST, Manage, Admin | 5 s | 60 s | 60 s | 5 s |
| Health | 5 s | 5 s | 5 s | 5 s |

A directly created `MLClient` derives Health with `_HEALTH_TIMEOUT`, independently
of the primary timeout. An explicit `health_config` timeout or request override
changes it. A manager's explicit timeout applies to every server, including
Health.

## Configuration precedence

Timeouts are Python HTTP options, not environment YAML settings. With a
[manager](../http-configuration.md), values resolve in this order, with each explicit value
replacing the previous one:

1. The selected server kind's default.
2. The manager's timeout.
3. The client-factory call's timeout.
4. The individual request's timeout.

At every level, omit the argument to inherit; pass a number or `httpx.Timeout`
to replace it, or `None` to disable it. Timeout components are not merged.

## Server execution limits and total duration

An HTTP timeout does not limit how long MarkLogic may execute a query. Server
settings such as a transaction's `time_limit` control that separately. In eval,
`timeout` is a transport option; use `variables={"timeout": value}` if your query
itself declares an external variable with that name.

Streaming, multiple requests, eligible retries and backoff can make an operation
last longer than one HTTP timeout. It is not a total wall-clock deadline.

Sessions compare effective timeout components before sharing a connection.
Separately constructed but equal timeouts are compatible; a disabled timeout
never shares with a bounded one.
