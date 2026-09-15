# HTTP configuration

Use these settings to control HTTP requests and connection pools in Python.
They are separate from the [environment YAML](environments.md), which stores server
connections and credentials. Start with the [manager basics](environments.md#use-it-from-python)
if you want to create clients from a named environment.

## Set it on a manager, a client, or a request

`retry`, `limits` and `timeout` are HTTP client options, **not environment settings**: none can be configured in the environment YAML. `limits` caps the connection pool - `max_connections` acts as a semaphore over concurrent requests - and `timeout` bounds each request. You set them at three levels, each overriding the one before it:

- **Manager** - a default for every client the manager creates, across all servers including Health.
- **Client** - on `MLClient` or `HTTPConfig` when creating a client directly, or as an override to a manager factory (`get_client`, `get_config`, ...) for the selected server.
- **Request** - `timeout` on an individual operation, bounding just that call. `retry` and `limits` resolve at the client, so they have no per-request form.

There is no YAML value beneath these levels. Set the manager defaults on construction and its factories:

```python
>>> import httpx
>>> from httpx_retries import Retry
>>> from mlclient import MLClientManager
>>> from mlclient.http import NO_RETRY_STRATEGY
>>> mgr = MLClientManager(
...     "local",
...     retry=Retry(total=2),
...     limits=httpx.Limits(max_connections=10),
...     timeout=httpx.Timeout(connect=5.0, read=120.0, write=60.0, pool=5.0),
... )
>>> with mgr.get_client("content") as ml:
...     result = ml.eval.xquery('"Hello World!"')
>>> with mgr.get_client("health", retry=NO_RETRY_STRATEGY) as ml:
...     healthy = ml.healthcheck()
```

A factory override wins over the manager default for that one client; pass `timeout` to a single operation to bound just that request:

```python
>>> with mgr.get_client("content") as ml:
...     result = ml.eval.xquery('"Hello World!"', timeout=5.0)
```

The options have different defaults and override semantics. Read
[timeouts](python/timeouts.md), [retries](python/retries.md) and
[resource limits](python/limits.md) for details. In particular, `timeout=None`
disables timeouts, while `retry=None` restores the server's default retry policy.

## Async clients, raw HTTP and resolved configuration

The same selection and override rules apply to `get_async_client()`, `get_http_client()` and `get_async_http_client()`. Raw HTTP factories require a server identifier:

```python
>>> mgr = MLClientManager("local")
>>> async with mgr.get_async_client("health") as ml:
...     healthy = await ml.healthcheck()
>>> with mgr.get_http_client("health") as http:
...     response = http.head("/")
```

Use `get_config()` to obtain a resolved `HTTPConfig` without creating a client or opening a session:

```python
>>> config = mgr.get_config("content", port=9100, retry=NO_RETRY_STRATEGY)
```

Overrides accept the parameters of `HTTPConfig.clone()`; unknown names raise `TypeError`. `get_config()` applies the same manager defaults and per-call overrides as the client factories.
