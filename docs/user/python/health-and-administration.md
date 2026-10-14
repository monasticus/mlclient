# Health, versions and administration


Check health and version before using administrative operations. The examples
below cover readiness checks, version information and restart waits.

## Health check

[healthcheck][mlclient.MLClient.healthcheck] reports whether MarkLogic's HealthCheck app server answers. That server is unauthenticated by design and returns `200 OK` only while the node is healthy - load balancers treat any other status as unhealthy.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     ml.healthcheck()
True
```

The probe maps the response to a verdict:

- `2xx` -\> `True` (healthy)
- `5xx` -\> `False` (server up but not ready)
- `4xx` -\> raises [HTTPStatusError](https://www.python-httpx.org/exceptions/); a client error means the request was misdirected (for example, aimed at an authenticated server), not that the node is unhealthy

By default, health checks use the client's host on port `7997`, without
authentication or retries, and with a 5-second timeout.

Pass an [HTTPConfig][mlclient.http.HTTPConfig] as `health_config` to use a separate
health connection. Its host, port, authentication and TLS settings are preserved.
Retry and timeout default independently to no retries and 5 seconds; explicit
values are preserved, including `timeout=None` to disable timeouts.


```python
>>> from mlclient import MLClient
>>> from mlclient.http import HTTPConfig

>>> health_config = HTTPConfig.resolve(
...     host="healthcheck.example.com",
...     port=7997,
...     auth=None,
... )
>>> with MLClient(host="ml.example.com", health_config=health_config) as ml:
...     ml.healthcheck()
True
```

## Server version

[version][mlclient.MLClient.version] returns an immutable [MarkLogicVersion][mlclient.models.MarkLogicVersion], resolved from `xdmp:version()` and cached after the first access. `str(version)` preserves the complete server version. `parts` is always a four-element tuple of numeric components in their original order, padded with `None` for missing components. Unpacking yields those same four values.

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     version = ml.version
>>> str(version)
'12.0.1'
>>> version.parts
(12, 0, 1, None)
>>> first, second, third, fourth = version
>>> fourth is None
True

>>> from mlclient.models import MarkLogicVersion
>>> version = MarkLogicVersion("10.0-9.5")
>>> str(version)
'10.0-9.5'
>>> version.parts
(10, 0, 9, 5)
```

When the connecting user lacks the eval privilege, the query fails and the Manage (`/manage/v2/properties`) then Admin (`/admin/v1/server-config`) endpoints are tried in turn. If none succeeds, the eval [MarkLogicError][mlclient.exceptions.MarkLogicError] is re-raised. A connection error propagates from the eval attempt without trying auxiliary servers. Unavailable endpoints and malformed fallback responses are skipped.

On [AsyncMLClient][mlclient.AsyncMLClient] the version is an awaitable method rather than a cached property, because resolving it performs I/O:

```python
>>> import asyncio
>>> from mlclient import AsyncMLClient

>>> async def get_version():
...     async with AsyncMLClient() as ml:
...         return (await ml.version()).parts
>>> asyncio.run(get_version())
(12, 0, 1, None)
```


## Wait for a restart

Some Management and Admin API operations return `202 Accepted` together with `Location: /admin/v1/timestamp` and a `restart` payload body. That payload contains one or more `last-startup` entries keyed by `host-id`. This indicates that MarkLogic accepted the request and that callers should verify readiness through the Admin timestamp endpoint on port `8001` before issuing follow-up administrative requests.

The timestamp endpoint is host-specific, not cluster-wide. MarkLogic documentation explicitly notes that if an operation restarts multiple hosts, the caller must iterate through the returned `host-id` and timestamp pairs and check each host separately. `MLClient.wait_for_restart()` does that internally: for multi-host restart responses it resolves host ids through `GET /manage/v2/hosts` and waits for all affected hosts in parallel. The current client host is probed immediately while the host mapping request is in flight, and the remaining host probes are started as soon as the mapping is available. If the current client host is one of the affected hosts, the method still waits for a timestamp newer than that host's own `last-startup` value before it returns.

Use [wait_for_restart][mlclient.MLClient.wait_for_restart] for this check:

```python
>>> from mlclient import MLClient

>>> with MLClient(port=8002) as ml:
...     resp = ml.http.delete(
...         "/manage/v2/servers/TestServer",
...         params={"group-id": "Default"},
...     )
...     ml.wait_for_restart(resp)
```

If you call [wait_for_restart][mlclient.MLClient.wait_for_restart] without a response, it performs a single readiness probe using a retry policy tuned for restart windows:

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
...     ml.wait_for_restart()
```

For multi-host restart responses, the method waits for all affected hosts before it returns.
