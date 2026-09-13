# Connection and authentication

MLClient models two independent concerns separately:

- **Connection** -- the transport: HTTP, HTTPS, mutual TLS, or MarkLogic Cloud. Chosen from `protocol`, `ssl` ([SSLConfig][mlclient.connection.SSLConfig] ), and `cloud` ([CloudConfig][mlclient.connection.CloudConfig] ).
- **Authentication** -- how the client proves its identity, chosen from `auth` with credentials supplied via `username` / `password`.

Both are validated when the client is constructed, so an unsupported combination raises [ConfigError][mlclient.exceptions.ConfigError] immediately rather than failing on the first request.

## Connection modes

| Mode | How to select it | Protocol / port |
|----|----|----|
| HTTP | default | `http` / `8000` |
| HTTPS | `protocol="https"` | `https` |
| Mutual TLS | `ssl=SSLConfig(cert_file=..., key_file=...)` | `https` |
| MarkLogic Cloud | `cloud=CloudConfig(api_key=..., base_path=...)` | `https` / `443` |

A client certificate implies HTTPS, so the protocol is inferred. MarkLogic Cloud forces HTTPS on port 443 and routes every API tier through the same gateway using the configured `base_path`. HTTP sessions are shared only when their complete configurations match; health checks normally use a separate session because their retry strategy differs. Passing a conflicting `protocol` or `port` raises [ConfigError][mlclient.exceptions.ConfigError].

```python
>>> from mlclient import MLClient
>>> from mlclient.connection import SSLConfig, CloudConfig

# Plain HTTP (default)
>>> ml = MLClient(host="ml.example.com", port=8000)

# HTTPS with server-certificate verification
>>> ml = MLClient(protocol="https", host="ml.example.com", port=8443)

# HTTPS verified against a custom CA bundle
>>> ml = MLClient(
...     protocol="https",
...     host="ml.example.com",
...     port=8443,
...     ssl=SSLConfig(verify="/etc/ssl/corp-ca.pem"),
... )

# Mutual TLS - the client certificate forces HTTPS
>>> ml = MLClient(
...     host="ml.example.com",
...     port=8443,
...     ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
... )

# Mutual TLS with an encrypted client key - key_password decrypts it
>>> ml = MLClient(
...     host="ml.example.com",
...     port=8443,
...     ssl=SSLConfig(
...         cert_file="/client.pem",
...         key_file="/client-key.pem",
...         key_password="my-key-passphrase",
...     ),
... )

# MarkLogic Cloud
>>> ml = MLClient(
...     host="my-org.marklogic.cloud",
...     cloud=CloudConfig(api_key="my-api-key", base_path="/ml/my-instance"),
... )
```

## Authentication methods

The `auth` parameter accepts a string shortcut, an [AuthConfig][mlclient.auth.AuthConfig] for methods that need more than a username and password, a custom [Auth](https://www.python-httpx.org/advanced/authentication/), or `None` for application-level auth. Credentials always come from `username` / `password` -- never from `AuthConfig`.

| `auth` value | Method | Credentials |
|----|----|----|
| `"digest"` (default) | HTTP digest | `username` / `password` |
| `"basic"` | HTTP basic | `username` / `password` |
| `"digestbasic"` | HTTP digest | `username` / `password` |
| `"certificate"` | Client certificate | `ssl` client cert |
| `"kerberos"` | Kerberos / SPNEGO | ambient ticket cache |
| `AuthConfig(method="oauth", token=...)` | OAuth 2.0 Bearer | pre-acquired token |
| `AuthConfig(method="kerberos", ...)` | Kerberos / SPNEGO | ambient ticket cache, custom SPN |
| `None` | application-level | none |
| a custom [Auth](https://www.python-httpx.org/advanced/authentication/) instance | custom | supplied by the handler |

`"certificate"` and `"kerberos"` are accepted as plain strings because they need no extra data: certificate identity comes from the `ssl` client cert, and Kerberos defaults to the `HTTP` service on the request host. Use `AuthConfig` only to override the Kerberos SPN (`service` / `hostname`), or for OAuth, which has no default token.

With mutual TLS, `auth` defaults to `"certificate"`, so it need not be set explicitly. Kerberos relies on the optional `pyspnego` dependency (`pip install mlclient[kerberos]`); the import is verified at client creation so a missing dependency fails early.

```python
>>> from mlclient import MLClient
>>> from mlclient.auth import AuthConfig
>>> from mlclient.connection import SSLConfig

# Digest (default) - explicit here for clarity
>>> ml = MLClient(auth="digest", username="my-user", password="my-password")

# Basic auth
>>> ml = MLClient(auth="basic", username="my-user", password="my-password")

# Client certificate - the cert is the identity, and forces HTTPS;
# auth defaults to "certificate", so setting it explicitly is optional
>>> ml = MLClient(
...     host="ml.example.com",
...     port=8443,
...     ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
... )

# Double auth - the client cert sets up mutual TLS as transport, but the
# user identity comes from a digest credential. Set auth explicitly to keep
# it instead of letting mutual TLS default it to "certificate".
>>> ml = MLClient(
...     host="ml.example.com",
...     port=8443,
...     auth="digest",
...     username="my-user",
...     password="my-password",
...     ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
... )

# OAuth 2.0 Bearer token
>>> ml = MLClient(auth=AuthConfig(method="oauth", token="jwt-token"))

# Kerberos / SPNEGO - credentials come from the ambient ticket cache
>>> ml = MLClient(protocol="https", auth="kerberos")

# Kerberos with a custom SPN - AuthConfig overrides service / hostname
>>> ml = MLClient(
...     protocol="https",
...     auth=AuthConfig(method="kerberos", service="HTTP", hostname="ml.example.com"),
... )

# Application-level auth - no HTTP auth header is added
>>> ml = MLClient(auth=None)

# A custom httpx.Auth handler is passed through unchanged
>>> import httpx
>>> ml = MLClient(auth=httpx.BasicAuth("my-user", "my-password"))
```

## Valid and rejected combinations

Validation rejects combinations MarkLogic cannot serve, and warns on ones that are valid but risky (basic auth over plain HTTP logs a cleartext-credentials warning rather than raising).

| Combination | Result | Reason |
|----|----|----|
| HTTP + digest / basic | valid | default credential auth |
| HTTPS + digest / basic / oauth / kerberos | valid | credential or token auth over TLS |
| Mutual TLS + certificate | valid | client certificate proves identity |
| Mutual TLS + explicit `auth="digest"` | valid | double auth: certificate plus digest header |
| Cloud + `auth=None` | valid | Cloud authenticates via its API key |
| `certificate` without a client cert | rejected | certificate auth requires a client cert over HTTPS |
| client cert + `protocol="http"` | rejected | mutual TLS requires HTTPS |
| Cloud + any explicit `auth` | rejected | Cloud handles authentication internally |
| Cloud + `protocol="http"` or custom `port` | rejected | Cloud forces HTTPS on port 443 |

A client certificate plays one of two roles. On its own it *is* the identity: mutual TLS defaults `auth` to `"certificate"` and no auth header is sent. Set `auth` to a credential method explicitly and the certificate drops to being just the transport - mutual TLS sets up the TLS channel while a digest or basic header carries the MarkLogic user identity. That second arrangement is *double auth*.

```python
>>> from mlclient import MLClient
>>> from mlclient.auth import AuthConfig
>>> from mlclient.connection import SSLConfig, CloudConfig
>>> from mlclient.exceptions import ConfigError

# Certificate auth without a client certificate
>>> try:
...     MLClient(auth=AuthConfig(method="certificate"))
... except ConfigError as exc:
...     print("rejected")
rejected

# A client certificate cannot be used over plain HTTP
>>> try:
...     MLClient(
...         protocol="http",
...         ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
...     )
... except ConfigError as exc:
...     print("rejected")
rejected

# A Cloud connection rejects an explicit auth method
>>> try:
...     MLClient(
...         host="my-org.marklogic.cloud",
...         cloud=CloudConfig(api_key="my-api-key", base_path="/ml/x"),
...         auth="digest",
...     )
... except ConfigError as exc:
...     print("rejected")
rejected
```

## Separate REST, Manage and Admin connections


MarkLogic exposes three separate HTTP API tiers, each bound to a fixed port:

| Tier              | Port        | Endpoints      |
|-------------------|-------------|----------------|
| Client (REST) API | 8000/custom | `/v1/*`        |
| Admin API         | 8001        | `/admin/v1/*`  |
| Management API    | 8002        | `/manage/v2/*` |

Port 8000 is the default App-Services REST server. Custom REST app servers (created via the Management API) also serve `/v1/*` on their configured port. Neither custom HTTP nor custom REST app servers serve `/manage/v2/*` or `/admin/v1/*` endpoints - those are only available on the fixed ports shown above. Port 8000 appears to accept `/manage/v2/*` requests, but it silently redirects them to port 8002.

`MLClient` reflects this topology through three API properties:

```text
MLClient (main entry point)
  +- .http       -> HttpClient   (raw HTTP on the main port)
  +- .rest       -> RestApi      (/v1/* on the main port)
  +- .manage     -> ManageApi    (/manage/v2/* on port 8002)
  +- .admin      -> AdminApi     (/admin/v1/* on port 8001)
  +- .parser     -> MLResponseParser
  +- .documents, .eval, .logs -> high-level services
```

Port routing is automatic: Manage defaults to 8002 and Admin to 8001. Their configurations inherit the primary settings except for the port (see [Manage or Admin on a different host or credentials](#manage-or-admin-on-a-different-host-or-credentials) to override this). `connect()` and entering a context open only the primary HTTP session. Auxiliary sessions open on their first request, not when accessing an API property. `disconnect()` and context exit close every opened session. Cached API objects can be reused after reconnecting. Outside a connected client's lifecycle, requests use short-lived sessions.

An auxiliary API reuses the primary session when its complete configuration matches, including injected configurations on custom ports. Matching includes host, connection mode, credentials, authentication, retry strategy, pool limits and timeout. Custom auth handlers and retry strategies must be the same object. Explicit limits and effective timeouts are compared by value, so independently constructed settings with equal components can share a session. Unset limits continue to defer to HTTPX defaults. Timeout and limits properties return copies. Change settings with `config.clone(timeout=..., limits=...)`; mutating a returned object does not change the configuration, its clones, presets or an already-open session.

```python
>>> from mlclient import MLClient

# Default port is 8000 - Manage requests use 8002, Admin requests use 8001
>>> with MLClient() as ml:
...     resp = ml.manage.databases.get_list()
...     ts = ml.admin.get_timestamp()

# Custom REST server on port 8040 - .rest uses 8040, .manage/admin use 8002/8001
>>> with MLClient(port=8040) as ml:
...     resp = ml.rest.eval.post(xquery="1")
...     dbs = ml.manage.databases.get_list()
```

### Manage or Admin on a different host or credentials

Derivation only changes the port; it keeps the primary host, protocol, and credentials. When the Manage or Admin tier lives on a different host, needs different credentials, or listens on a non-standard port (for example behind a reverse proxy), pass a fully resolved [HTTPConfig][mlclient.http_config.HTTPConfig] as `manage_config` or `admin_config`. That tier then uses the given configuration as-is instead of deriving one from the primary connection; the other tier keeps deriving as usual.

```python
>>> from mlclient import MLClient
>>> from mlclient.http_config import HTTPConfig

# Manage lives behind a proxy on a different host and port;
# .admin is still derived from the primary connection (localhost:8001)
>>> manage_config = HTTPConfig.resolve(
...     host="manage-proxy.example.com",
...     port=9002,
...     username="manage-user",
...     password="manage-password",
... )
>>> with MLClient(host="ml.example.com", manage_config=manage_config) as ml:
...     dbs = ml.manage.databases.get_list()
...     ts = ml.admin.get_timestamp()
```
