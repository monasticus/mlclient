# Connection and authentication

MLClient models two independent concerns separately:

- **Connection** -- the transport: HTTP, HTTPS, mutual TLS, or MarkLogic Cloud. Chosen from `protocol`, `ssl` ([SSLConfig][mlclient.connection.SSLConfig] ), and `cloud` ([CloudConfig][mlclient.connection.CloudConfig] ).
- **Authentication** -- how the client proves its identity, chosen from `auth` with credentials supplied via `username` / `password`.

Local configuration is validated when the client is constructed: conflicting
transport/auth settings raise [ConfigError][mlclient.exceptions.ConfigError].
MLClient does not contact the server to discover its version or reject an auth
method based on that version. The target App Server must support and be configured
for the selected method; server authentication errors propagate normally.

## Connection modes

| Mode | How to select it | Protocol / port | Server availability |
|----|----|----|----|
| HTTP | default | `http` / `8000` | MarkLogic 10, 11, 12 |
| HTTPS | `protocol="https"` | `https` | MarkLogic 10, 11, 12; server certificate configured |
| Mutual TLS | `ssl=SSLConfig(cert_file=..., key_file=...)` | `https` | MarkLogic 10, 11, 12; trusted client CA configured |
| MarkLogic Cloud | `cloud=CloudConfig(api_key=..., base_path=...)` | `https` / `443` | Managed Cloud gateway; not selected by server major version |

These tables describe availability within the MarkLogic 10–12 range covered by
MLClient's [integration matrix](../../stability.md#supported-and-tested-versions),
not the release in which each older transport/auth method first appeared. TLS
versions and cipher support depend on the server release and configuration.

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

| `auth` value | Method | Credentials | Server availability |
|----|----|----|----|
| `"digest"` (default) | HTTP digest | `username` / `password` | MarkLogic 10, 11, 12 |
| `"basic"` | HTTP basic | `username` / `password` | MarkLogic 10, 11, 12 |
| `"digestbasic"` | HTTP digest | `username` / `password` | MarkLogic 10, 11, 12 |
| `"certificate"` | Client certificate | `ssl` client cert | MarkLogic 10, 11, 12 |
| `"kerberos"` | Kerberos / SPNEGO | ambient ticket cache | MarkLogic 10, 11, 12 |
| `AuthConfig(method="oauth", token=...)` | OAuth 2.0 Bearer | pre-acquired token | JWT Resource Server: **11.2+**; unavailable on 10 |
| `AuthConfig(method="kerberos", ...)` | Kerberos / SPNEGO | ambient ticket cache, custom SPN | MarkLogic 10, 11, 12 |
| `None` | application-level | none | MarkLogic 10, 11, 12 |
| a custom [Auth](https://www.python-httpx.org/advanced/authentication/) instance | custom | supplied by the handler | Depends on the target server or gateway |

MarkLogic 10's [App Server authentication settings](https://docs.marklogic.com/10.0/admin:appserver-set-authentication)
include the credential, certificate and Kerberos methods above, but not OAuth.
The JWT Resource Server flow used by the integration tests requires MarkLogic
11.2 or later. Earlier 11.x OAuth flows and the `sec:oauth-server` signature
differ; see the OAuth changes in the [MarkLogic 11 release notes](https://docs.marklogic.com/11.0/guide/release-notes.pdf).
MLClient only sends the supplied Bearer token; it does not configure external
security, acquire OAuth tokens, or maintain a server-version compatibility gate.

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

Validation rejects locally inconsistent combinations and warns on ones that are
valid but risky (basic auth over plain HTTP logs a cleartext-credentials warning
rather than raising). A valid configuration still requires the server support
and setup listed above, including MarkLogic 11.2+ for JWT Resource Server auth.

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

## API tiers on separate connections

MLClient reflects MarkLogic's three API tiers (REST, Manage, Admin) as separate
connections - see [Clients](../clients.md#server-tiers-and-ports) for the tiers,
their ports and automatic routing. This section covers how those auxiliary
connections derive from and share the primary session.

`connect()` and entering a context open only the primary HTTP session. Auxiliary sessions open on their first request, not when accessing an API property. `disconnect()` and context exit close every opened session. Cached API objects can be reused after reconnecting. Outside a connected client's lifecycle, requests use short-lived sessions.

An auxiliary API reuses the primary session when its complete configuration matches, including injected configurations on custom ports. Matching includes host, connection mode, credentials, authentication, retry strategy, pool limits and timeout. Custom auth handlers and retry strategies must be the same object. Explicit limits and effective timeouts are compared by value, so independently constructed settings with equal components can share a session. Unset limits continue to defer to HTTPX defaults. Timeout and limits properties return copies. Change settings with `config.clone(timeout=..., limits=...)`; mutating a returned object does not change the configuration, its clones, presets or an already-open session.

### Manage or Admin on a different host or credentials

Derivation only changes the port; it keeps the primary host, protocol, and credentials. When the Manage or Admin tier lives on a different host, needs different credentials, or listens on a non-standard port (for example behind a reverse proxy), pass a fully resolved [HTTPConfig][mlclient.http.HTTPConfig] as `manage_config` or `admin_config`. That tier then uses the given configuration as-is instead of deriving one from the primary connection; the other tier keeps deriving as usual.

```python
>>> from mlclient import MLClient
>>> from mlclient.http import HTTPConfig

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
