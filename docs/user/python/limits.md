# Resource limits

Set connection-pool limits when creating a client:

```python
from mlclient import MLClient

with MLClient(limits=20) as ml:
    result = ml.eval.xquery('"Hello World!"')
```

An int is shorthand for the concurrency cap: `limits=20` means
`max_connections=20`, leaving the other pool settings at their httpx defaults.
Use `httpx.Limits` to set them independently:

```python
import httpx
from mlclient import MLClient

limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
with MLClient(limits=limits) as ml:
    result = ml.eval.xquery('"Hello World!"')
```

The same option is accepted by `AsyncMLClient`, `HTTPConfig` and
[manager factories](../http-configuration.md). It is configured in Python, not environment YAML.

## Pool settings

- `max_connections`: maximum concurrent connections, including active and idle ones.
- `max_keepalive_connections`: maximum idle connections kept for reuse.
- `keepalive_expiry`: how long an idle connection can be reused, in seconds.

When `limits` is omitted or `None`, MLClient leaves it to HTTPX. With the currently
supported HTTPX version, defaults are 100 connections, 20 idle connections and a
five-second keep-alive expiry.

## Limits and concurrency

A pool limit bounds connections, not the number of tasks created by your
application. If all connections are busy, a request waits for one according to
its pool [timeout](timeouts.md). For large workloads, also bound the work you
schedule; the [concurrent eval recipe](../../recipes.md#evaluate-queries-across-databases-concurrently)
shows this for queries against several databases.

## Separate API connections

Limits apply per underlying HTTP transport. REST, Manage, Admin and Health can
use separate transports, each with its own pool. Configurations can share a
session only when their effective connection settings are compatible, including
pool limits and timeout values.

Changing an `httpx.Limits` object after creating a client does not reconfigure
that client's pool. Supply the desired limits when creating the client or use
`HTTPConfig.clone(limits=...)` to prepare a new configuration.
