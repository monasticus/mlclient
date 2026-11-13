# Retries

Set retries when creating a client:

```python
from mlclient import MLClient

with MLClient(retry=2) as ml:
    response = ml.http.get("/v1/documents", params={"uri": "/hello.json"})
```

An int is shorthand for the retry count: `retry=2` allows up to two retries and
`retry=0` disables them. Use `httpx_retries.Retry` to also configure backoff and
eligibility:

```python
from httpx_retries import Retry
from mlclient import MLClient

with MLClient(retry=Retry(total=2, backoff_factor=0.5)) as ml:
    response = ml.http.get("/v1/documents", params={"uri": "/hello.json"})
```

Retry settings belong to the Python HTTP configuration, not environment YAML.

## Default policy

`DEFAULT_RETRY_STRATEGY` allows up to five retries with a backoff factor of `0.5`.
A failed request is retried only when all of these hold:

- the method is idempotent - `HEAD`, `GET`, `PUT`, `DELETE`, `OPTIONS` or `TRACE`.
  `POST` is never retried, so eval, invoke and `POST /v1/search` run once;
- the request failed before the server could process it, or the connection was
  aborted: `httpx.ConnectTimeout`, `httpx.WriteTimeout`, `httpx.PoolTimeout`,
  `httpx.NetworkError` (`ConnectError`, `ReadError`, `WriteError`, `CloseError`)
  or `httpx.RemoteProtocolError` (the server closed the connection without a
  response), or the response status is `429`, `502` or `503`.

A read timeout (`httpx.ReadTimeout`) and `504 Gateway Timeout` are **not**
retried. In both cases the server got the request and is most likely still
running it: the client stopped waiting, or a proxy in front of MarkLogic (an
AWS ALB, nginx) gave up after its idle timeout - MarkLogic itself never returns
`504`. A retry would start the same slow request again on the server and multiply
the wait before the error. Raise the [timeout](timeouts.md) instead, or the
proxy's idle timeout.

A proxy can also return `504` when it could not reach MarkLogic at all, for
example a node that is down but still registered behind an ALB. The default
policy does not retry that either. To retry it, pass your own strategy:

```python
import httpx
from httpx_retries import Retry
from mlclient import MLClient

retry = Retry(
    total=5,
    backoff_factor=0.5,
    retry_on_exceptions=[
        httpx.ConnectTimeout,
        httpx.WriteTimeout,
        httpx.PoolTimeout,
        httpx.NetworkError,
        httpx.RemoteProtocolError,
    ],
    status_forcelist=[429, 502, 503, 504],
)
with MLClient(retry=retry) as ml:
    response = ml.http.get("/v1/documents", params={"uri": "/hello.json"})
```

Add `httpx.ReadTimeout` to `retry_on_exceptions` the same way to retry read
timeouts. A `Retry` built without `retry_on_exceptions` or `status_forcelist`
uses the `httpx-retries` defaults, which include both. The int shorthand is such a
`Retry`: `retry=2` is `Retry(total=2)` and retries read timeouts and `504`.

HealthCheck uses `NO_RETRY_STRATEGY` by default so a probe returns promptly.
For an explicit `health_config`, an omitted retry strategy still resolves to no
retries; an explicitly supplied strategy is preserved.

## Disable retries

```python
from mlclient import MLClient
from mlclient.http import NO_RETRY_STRATEGY

with MLClient(retry=NO_RETRY_STRATEGY) as ml:
    response = ml.http.get("/v1/documents", params={"uri": "/hello.json"})
```

Passing `retry=None` restores the default policy; it does **not** disable retries.

## Set a manager policy

A manager's explicit policy applies to every connection, including Health.
Override it when requesting an individual client:

```python
from httpx_retries import Retry
from mlclient import MLClientManager

manager = MLClientManager("local", retry=Retry(total=2))
with manager.get_client("health", retry=None) as ml:
    healthy = ml.healthcheck()
```

Here `retry=None` restores Health's no-retry default. For another server kind,
it restores `DEFAULT_RETRY_STRATEGY`. Per-call overrides do not change later
clients created by the manager.

## Retry timing

Retries and backoff can make an operation take longer than a single request's
[timeout](timeouts.md). An HTTP timeout limits individual transport phases;
it is not a deadline for the entire retry sequence.
