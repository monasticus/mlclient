# Health, versions and administration

Some Management and Admin API operations return `202 Accepted` together with `Location: /admin/v1/timestamp` and a `restart` payload body. That payload contains one or more `last-startup` entries keyed by `host-id`. This indicates that MarkLogic accepted the request and that callers should verify readiness through the Admin timestamp endpoint on port `8001` before issuing follow-up administrative requests.

The timestamp endpoint is host-specific, not cluster-wide. MarkLogic documentation explicitly notes that if an operation restarts multiple hosts, the caller must iterate through the returned `host-id` and timestamp pairs and check each host separately. `MLClient.wait_for_restart()` does that internally: for multi-host restart responses it resolves host ids through `GET /manage/v2/hosts` and waits for all affected hosts in parallel. The current client host is probed immediately while the host mapping request is in flight, and the remaining host probes are started as soon as the mapping is available. If the current client host is one of the affected hosts, the method still waits for a timestamp newer than that host's own `last-startup` value before it returns.

Use [wait_for_restart][mlclient.MLClient.wait_for_restart] for this check:

```python
>>> from mlclient import MLClient

>>> with MLClient() as ml:
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

# Health check

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

By default, health checks use a configuration derived from the primary configuration, overriding the port to `7997`, authentication to none, retry to `NO_RETRY_STRATEGY` and timeout to `HEALTH_TIMEOUT` (5 seconds) - the health probe uses `HEALTH_TIMEOUT` regardless of the primary client's timeout. These defaults also apply when the primary already targets `7997`; an identical effective configuration reuses its session. Cloud connections retain their gateway port and Cloud authentication, while health requests still default to no retries. [healthcheck][mlclient.MLClient.healthcheck] accepts a keyword-only `timeout` to override the probe's default for a single call.

Pass a resolved [HTTPConfig][mlclient.http_config.HTTPConfig] as `health_config` to supply the health connection explicitly. Its host, port, authentication and TLS settings are preserved. Retry and timeout resolve independently: when `retry` was omitted, health requests use `NO_RETRY_STRATEGY`, and when `timeout` was omitted they use `HEALTH_TIMEOUT`; an explicitly supplied strategy or timeout is preserved, including `None` (which disables every HTTP timeout). `HTTPConfig.clone()` retains whether each was explicitly configured; `has_explicit_retry` and `has_explicit_timeout` expose that distinction without changing the normal defaults for other requests.

```python
>>> from mlclient import MLClient
>>> from mlclient.http_config import HTTPConfig

>>> health_config = HTTPConfig.resolve(
...     host="healthcheck.example.com",
...     port=7997,
...     auth=None,
... )
>>> with MLClient(host="ml.example.com", health_config=health_config) as ml:
...     ml.healthcheck()
True
```

# Server version

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

>>> from mlclient import MarkLogicVersion
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

Numeric components have no universal major/minor/patch/hotfix labels because MarkLogic's versioning scheme changed between releases. Textual suffixes are preserved by `str(version)` and excluded from `parts`. An invalid eval version raises `ValueError`.

## Log-level configuration

The synchronous [LogLevelService][mlclient.services.LogLevelService] supports the `log-level` CLI command and can also be constructed with a client's API handles:

```python
>>> from mlclient import MLClient
>>> from mlclient.services import LogLevelService
>>> with MLClient(username="admin", password="admin") as ml:
...     levels = LogLevelService(ml.rest, ml.manage)
...     current = levels.get(group="Default", log_type="file")
...     levels.set(current, group="Default", log_type="file")
```

Omit `server` to target a group, or supply an App Server name for its file log level. App Servers have no system log level. Names and levels are sent as external variables. Evaluation through the REST server is attempted first; only authorization failures trigger Management REST fallback. Transport and other server errors propagate. See [log-level](../cli/log-level.md) for supported levels and Management permissions.

Both `get` and `set` accept a keyword-only `timeout`:

```python
>>> with MLClient(timeout=10) as ml:
...     levels = LogLevelService(ml.rest, ml.manage)
...     current = levels.get(timeout=2)
...     levels.set(current, timeout=None)
```

Omitting `timeout` uses the configuration of whichever client sends the request (REST or Manage). An explicit number, `httpx.Timeout` or `None` is forwarded to both eval and any Management fallback. Each request has its own timeout; this is not a total deadline across both requests. Overrides do not change subsequent calls. A transport timeout propagates without triggering Management fallback.

The group API wrappers also accept `timeout` on `get_properties` and `put_properties`, for both `ml.manage.groups` and the asynchronous client.
