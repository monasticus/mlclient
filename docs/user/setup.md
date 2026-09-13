# Environments and runtime settings

When using **ML Client** in your application it can be helpful to setup **ML Client**'s environment. It will make it easier to use `mlclient` lib without explicit use of ML configuration parameters. Using a YAML file, you're able to easily get a configuration for a MLClient instance.

## YAML Environment file

Assume you want to manage your ML application called *migration-app*. First create a `.mlclient` directory in root of your project and a YAML file within:

    migration-app
    ├── .mlclient
    │   └── mlclient-local.yaml
    ├── src
    ├── tests
    └── pyproject.toml

YAML file:

```yaml
--8<-- "user/setup/mlclient-local.yaml"
```

[Download the configuration](setup/mlclient-local.yaml)

## Root-level defaults and per-server overrides

Connection and authentication settings declared at the top level of the file (`protocol`, `host`, `username`, `password`, `auth`, `ssl`, `cloud`) act as defaults for every app server. Any of `auth`, `username`, `password`, or `ssl` may be overridden per server; an unset field inherits the root value. `auth`, `username` and `password` replace the root value wholesale, while `ssl` merges field by field: a server declaring only a client certificate keeps the root's server verification (see below). This mirrors the [MLClient][mlclient.MLClient] connection model - see [connection and authentication](python/connections.md) for the full matrix of connection modes and auth methods. For example, an HTTPS environment with a mutual-TLS app server:

> ```yaml
> app-name: migration-app
> protocol: https
> host: ml.example.com
> username: admin
> password: admin
> auth: digest
> ssl:
>   verify: /etc/ssl/corp-ca.pem
> app-servers:
>
>   - id: content
>     port: 8100
>
>   - id: secure
>     port: 8200
>     ssl:
>       cert_file: /client.pem
>       key_file: /client-key.pem
> ```

The `content` server inherits the root digest auth and CA bundle, while `secure` presents a client certificate and so authenticates via mutual TLS. Because `ssl` merges, `secure` keeps the root's `verify: /etc/ssl/corp-ca.pem` even though it only declares `cert_file` and `key_file`. A server overrides a single SSL field by setting it explicitly - `verify: /etc/ssl/other-ca.pem` for a different CA bundle, or `verify: false` to disable server verification for that server alone - while every unset field still inherits from the root.

The `auth` field accepts the Python API shortcuts `digest`, `basic`, `digestbasic`, `certificate`, and `kerberos`, plus the YAML alias `app`. A server presenting a client certificate can set `auth: certificate` explicitly, or use a credential method such as `auth: digest` for double auth. An omitted server `auth` inherits the root setting, which defaults to `digest`.

Use `auth: app` when MarkLogic performs application-level authentication. MLClient then sends no HTTP authentication header and MarkLogic uses the App Server's configured default user.

A MarkLogic Cloud environment declares `cloud` at the root and omits `protocol` and `auth` (Cloud forces HTTPS and authenticates via its API key). Cloud collapses every tier onto a single HTTPS connection on port 443, routing each one through the `base-path` rather than a distinct port. Because there is only one connection and its port is fixed, a Cloud environment needs no `app-servers` section at all - the default REST app server is enough:

> ```yaml
> app-name: migration-app
> host: my-org.marklogic.cloud
> cloud:
>   api-key: my-api-key
>   base-path: /ml/my-instance
> ```

`port` is optional everywhere and defaults to the connection's own port (8000 for on-premises, 443 for Cloud), so it need only be set for app servers on a non-default port. Declare `app-servers` explicitly only to name additional servers or override per-server settings.

Four app servers are always present even when you list none: `app-services` (the port-8000 REST server), `manage` (8002), `admin` (8001), and `health` (7997, application-level auth). Anything you declare is added to them; an entry whose `id` matches one of the four overrides that predefined server - for example, declaring `admin` on a non-standard port or `app-services` with `rest: false`.

## MLEnvironment class

Having the environment file, you can instantiate `MLEnvironment` class using your environment:

    >>> from mlclient import MLEnvironment
    >>> env = MLEnvironment.load("local")
    >>> env
    MLEnvironment(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', auth='digest', ssl=None, cloud=None, app_servers=[MLServerConfig(identifier='manage', port=8002, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='content', port=8100, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='modules', port=8101, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='schemas', port=8102, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='test', port=8103, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='app-services', port=None, protocol=None, auth=None, username=None, password=None, ssl=None, rest=True), MLServerConfig(identifier='admin', port=8001, protocol=None, auth=None, username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='health', port=7997, protocol=None, auth=None, username=None, password=None, ssl=None, rest=False)])

This code will work in every subdirectory of the `migration-app` project as it looks for `.mlclient` recursively.

`MLEnvironment` class allows you to get a specific app service config:

    >>> from mlclient import MLClient, MLEnvironment
    >>> env = MLEnvironment.load("local")
    >>> with MLClient(config=env.provide_config("content")) as ml:
    ...     result = ml.eval.xquery("xdmp:database() => xdmp:database-name()")
    ...

!!! note
    If you want to load an environment from a specific file path instead of relying on the `.mlclient` directory lookup, you can use `MLEnvironment.load_file()`:

        >>> from mlclient import MLEnvironment
        >>> env = MLEnvironment.load_file("path/to/mlclient-local.yaml")
        >>> env

    MLEnvironment(app_name='migration-app', protocol='http', host='localhost', username='admin', password='admin', auth='digest', ssl=None, cloud=None, app_servers=\[MLServerConfig(identifier='manage', port=8002, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='content', port=8100, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='modules', port=8101, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='schemas', port=8102, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='test', port=8103, protocol=None, auth='basic', username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='app-services', port=None, protocol=None, auth=None, username=None, password=None, ssl=None, rest=True), MLServerConfig(identifier='admin', port=8001, protocol=None, auth=None, username=None, password=None, ssl=None, rest=False), MLServerConfig(identifier='health', port=7997, protocol=None, auth=None, username=None, password=None, ssl=None, rest=False)\])

## MLClientManager class

`MLClientManager` loads a named ML Client Environment and creates clients with its connection settings. For example, `"local"` selects `.mlclient/mlclient-local.yaml` using the directory lookup described above.

### Basic manager usage

Select a configured App Server and use the client as a context manager:

```python
>>> from mlclient import MLClientManager
>>> mgr = MLClientManager("local")
>>> with mgr.get_client("content") as ml:
...     result = ml.eval.xquery("xdmp:database() => xdmp:database-name()")
```

Omit the identifier to select the first configured REST server:

```python
>>> with mgr.get_client() as ml:
...     result = ml.eval.xquery("1 + 1")
```

An explicit identifier can select any configured server, including `health`, `manage` and `admin`; it does not need to be marked as a REST server:

```python
>>> with mgr.get_client("health") as ml:
...     healthy = ml.healthcheck()
>>> with mgr.get_client("manage") as ml:
...     response = ml.manage.databases.get_list()
```

The selected server becomes the primary HTTP endpoint. Its corresponding API reuses that session, including custom ports and credentials. Other APIs retain their own environment settings. Entering the context opens only the primary session; auxiliary sessions open on their first request. Context exit closes all opened sessions.

### Overriding environment settings in Python

Settings such as `host`, `port` and `username` can come from the environment file. To change them for a particular use without editing YAML, pass overrides to the manager or its client factory:

```python
>>> mgr = MLClientManager("local", host="gateway.example.com")
>>> with mgr.get_client("content", port=9100) as ml:
...     result = ml.eval.xquery("1 + 1")
```

Here every server uses `gateway.example.com`, while only `content` uses port `9100`. Manage, Admin and Health retain their configured ports.

For settings present in the environment, precedence is: environment, manager overrides, then per-call overrides. Manager overrides apply to every server; per-call overrides apply only to the selected server and its corresponding API. For example, `get_client("manage", port=9002)` uses port `9002` for both `ml.http` and `ml.manage`. Neither the YAML file nor subsequent calls are modified by per-call overrides.

### Configuring HTTP retry, limits and timeout in Python

`retry`, `limits` and `timeout` are HTTP client options, **not environment settings**: none can be configured in the environment YAML. `limits` caps the connection pool - `max_connections` acts as a semaphore over concurrent requests - and `timeout` bounds each request. Set them on `MLClient` or `HTTPConfig` when creating a client directly, or through the manager and its factories:

```python
>>> import httpx
>>> from httpx_retries import Retry
>>> from mlclient.clients.http_client import NO_RETRY_STRATEGY
>>> mgr = MLClientManager(
...     "local",
...     retry=Retry(total=2),
...     limits=httpx.Limits(max_connections=10),
...     timeout=httpx.Timeout(connect=5.0, read=120.0, write=60.0, pool=5.0),
... )
>>> with mgr.get_client("content") as ml:
...     result = ml.eval.xquery("1 + 1")
>>> with mgr.get_client("health", retry=NO_RETRY_STRATEGY) as ml:
...     healthy = ml.healthcheck()
```

The manager's values apply to every server, including Health; a per-call value overrides it for the selected server. There is no YAML value underneath these two levels.

They differ in their defaults. Without an explicit retry strategy, the manager uses `NO_RETRY_STRATEGY` for `health` and `DEFAULT_RETRY_STRATEGY` for other servers; passing `retry=None` per call restores that server's default even when the manager specifies a strategy. `timeout` defaults to `HEALTH_TIMEOUT` for health and `DEFAULT_TIMEOUT` for other servers when left unset. `limits` has no library default: when unset it is not passed to the transport and `httpx` applies its own default (`max_connections=100`, `max_keepalive_connections=20`).

```python
>>> with mgr.get_client("health", retry=None) as ml:
...     healthy = ml.healthcheck()  # No retries despite the manager's setting.
```

### Timeout: values, inheritance and per-request overrides

`timeout` is a Python HTTP client setting, never an environment YAML value. It resolves through four levels, each overriding the one below it: the per-server-kind default, the manager's explicit value, the factory-call value, and the per-request value passed to an individual operation. Every level accepts the same forms:

- unset (the default) - inherit the level below, ending at the selected server's default;
- a number - set all four components to that many seconds;
- an `httpx.Timeout` - set the four components independently, no merge;
- `None` - **disable** every HTTP timeout, which is not the same as leaving it unset.

An `httpx.Timeout` has four independent components: `connect` (waiting for the socket to open), `read` (waiting between chunks of the response), `write` (waiting between chunks of the request body) and `pool` (waiting for a free connection from the pool). A bare number sets all four.

Without an explicit value, the `health` server uses `HEALTH_TIMEOUT` (5 seconds on all components) and every other server uses `DEFAULT_TIMEOUT` (`connect=5`, `read=60`, `write=60`, `pool=5`). A `MLClient` created directly derives health with `HEALTH_TIMEOUT` regardless of its main timeout, unless an explicit `health_config` timeout or per-request override is supplied; a manager's explicit `timeout` applies to every server including health.

Every operation accepts a keyword-only `timeout` that overrides the client default for that one request without mutating shared configuration:

```python
>>> import httpx
>>> with MLClientManager("local").get_client("content") as ml:
...     ml.eval.xquery("1 + 1", timeout=2)                 # 2s on all four components
...     ml.eval.xquery("1 + 1", timeout=httpx.Timeout(5.0, read=120.0))  # slow read only
...     ml.documents.read("/doc.xml", timeout=None)        # no timeout
...     ml.healthcheck(timeout=2)                          # override the 5s health probe
```

Three separate limits are easy to confuse:

- the **HTTP timeout** limits waiting in the connect, read, write and pool phases; read and write limits apply between chunks, not to the whole body;
- a **server-side execution limit** (for example a transaction's `time_limit`, or a request's server `time-limit`) bounds work inside MarkLogic and is unrelated to this setting;
- the **total wall-clock time** of an operation is not an HTTP timeout. Streaming, multiple requests, eligible retries and backoff can all extend an operation beyond its configured timeout. Not every timed-out request is retried: the configured retry policy determines which failures qualify.

Session sharing compares the effective timeout by its four components, so separately built but equal timeouts still share a session; a disabled timeout never shares with a bounded one.

### Async clients, raw HTTP and resolved configuration

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
