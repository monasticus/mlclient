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
Eligibility depends on the method, response status or exception according to
`httpx-retries`; a failed request is not automatically retried just because a
retry budget remains.

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
