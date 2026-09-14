# More on environments

Start with the [environment guide](../environments.md) for a basic YAML file and Python
usage. This page is the complete environment configuration guide: YAML fields,
inheritance, and creating or customizing configuration in Python. The
[connections and authentication guide](connections.md) describes supported
transport/authentication combinations and their requirements.

## YAML fields

An environment file is a mapping. These are all supported root keys; omit a key
to use its default. The names below are the YAML names, including hyphens.

| Key | Value | Default |
| --- | --- | --- |
| `app-name` | Application label used to scope discovery | `null` |
| `host` | Hostname or IP address | `localhost` |
| `protocol` | `http` or `https` | `http` |
| `username` | Username for credential-based authentication | `admin` |
| `password` | Password for credential-based authentication | `admin` |
| `auth` | Method name, authentication mapping, or `null` | `digest` |
| `ssl` | TLS mapping described below, or `null` | `null` |
| `cloud` | Cloud gateway mapping described below, or `null` | `null` |
| `app-servers` | List of connection mappings | The four predefined connections below |

Each `app-servers` entry supports these keys:

| Key | Value | Default when omitted |
| --- | --- | --- |
| `id` | Connection identifier used by the CLI and manager | Required |
| `port` | Integer port | Connection default: 8000, or 443 for Cloud |
| `rest` | Whether the connection is a default REST candidate | `false` |
| `protocol` | `http` or `https` | Inherit root |
| `username`, `password` | Credentials | Inherit root |
| `auth` | Method name, authentication mapping, or `null` | Inherit root |
| `ssl` | TLS mapping | Inherit root |

Use distinct identifiers. An identifier is a local connection label, not
necessarily the App Server's name in MarkLogic. Root `host` applies to every
entry; use Python overrides when a connection needs another host.

The environment models currently ignore unknown keys. Only the fields listed
here affect configuration; putting `timeout`, `retry` or `limits` in YAML does
not configure HTTP behavior. Values are parsed when loading the environment;
connection/authentication combinations are validated when resolving a connection.

## Root defaults and server overrides

Root settings apply to the environment's connections. An App Server entry can
override the fields listed below:

| Setting | Root | Per server | Override behavior |
| --- | --- | --- | --- |
| `host` | Yes | No | Use a Python override for a server on another host |
| `protocol` | Yes | Yes | A non-null server value replaces the root value |
| `username`, `password` | Yes | Yes | Non-null server values replace root credentials |
| `auth` | Yes | Yes | An explicit server value replaces the root method |
| `ssl` | Yes | Yes | Explicit server fields merge into root SSL settings |
| `cloud` | Yes | No | Configures the environment's Cloud gateway |
| `port` | No | Yes | Sets the connection port |
| `id`, `rest` | No | Yes | Identify a connection and mark default REST candidates |
| `app-name` | Yes | No | Labels the application |

An omitted server `auth` inherits the root method. `auth: app` or an explicit
`auth: null` disables HTTP authentication. For other nullable server fields,
null inherits the root value; an empty username or password is an explicit value.

For example, use one identity for REST and another for Manage:

```yaml
host: ml.example.com
protocol: https
username: app-user
password: app-password
auth: digest
app-servers:
  - id: app-services
    port: 8100
    rest: true
  - id: manage
    port: 8002
    username: manage-user
    password: manage-password
    auth: basic
```

The `manage` entry inherits HTTPS and the host, while replacing credentials and
authentication. These are connection settings; the corresponding server must
already be configured to accept them.

## Predefined connections

These connections are added when absent. Declaring a matching `id` replaces that
entry; declaring a new `id` adds a connection.

| Identifier | Default port | Purpose |
| --- | --- | --- |
| `app-services` | 8000 | Default REST App Server |
| `manage` | 8002 | Management API |
| `admin` | 8001 | Admin API |
| `health` | 7997 | HealthCheck, without HTTP authentication |

A replacement entry uses the normal field defaults: include `rest: true` when
replacing a connection that should remain eligible for default REST selection.
The first declared REST connection is the default; an explicit identifier can
select any connection, even one with `rest: false`.

For a custom connection with no port, the connection default is 8000 on premises
or 443 for Cloud. To use a custom Manage or Admin port, specify it in that entry.

## TLS and client certificates

The root `ssl` object sets TLS defaults. Per-server `ssl` merges only explicitly
specified fields, so a client certificate can be added without losing the root
CA configuration:

```yaml
host: ml.example.com
protocol: https
username: app-user
password: app-password
auth: digest
ssl:
  verify: /certs/server-ca.pem
app-servers:
  - id: content
    port: 8100
    rest: true
  - id: secure
    port: 8200
    rest: true
    auth: certificate
    ssl:
      cert_file: /certs/client.pem
      key_file: /certs/client-key.pem
```

`content` uses Digest over HTTPS. `secure` inherits the CA bundle and authenticates
with its client certificate. If `secure` instead inherits or explicitly selects
`auth: digest`, it presents the TLS certificate **and** uses Digest credentials.

| SSL key | Value | Default |
| --- | --- | --- |
| `verify` | `true`, `false`, or a CA-bundle path | `true` |
| `cert_file` | Client certificate path | `null` |
| `key_file` | Separate private-key path; omit if included in the certificate file | `null` |
| `key_password` | Password for an encrypted private key | `null` |

Use `verify: false` only when deliberately disabling server certificate verification.
An explicitly supplied `null` for a nullable SSL field clears that inherited field. A server can replace
that field while retaining the root's other SSL fields. For certificate formats,
validation rules and examples, see [connection modes](connections.md#connection-modes).

## Authentication settings

Use a method name for `basic`, `digest`, `digestbasic`, `certificate` or `kerberos`.
The YAML-only `app` alias means no HTTP authentication. Credential methods use
the environment or server's `username` and `password`.

An authentication mapping supports all of these fields:

| Auth key | Value | Default |
| --- | --- | --- |
| `method` | Authentication mechanism | Required |
| `token` | Pre-acquired bearer token for `oauth` | `null` |
| `service` | Kerberos SPN service component | `HTTP` |
| `hostname` | Kerberos SPN hostname override | Request host when omitted |

Basic and Digest credentials belong in `username` and `password`, outside this
mapping. Additional fields apply only to their corresponding mechanism.

Methods requiring additional data use an `auth` mapping. For an OAuth bearer token:

```yaml
host: ml.example.com
protocol: https
auth:
  method: oauth
  token: my-access-token
```

For a custom Kerberos service principal:

```yaml
host: ml.example.com
auth:
  method: kerberos
  service: HTTP
  hostname: kerberos-host.example.com
```

An `auth` mapping replaces the inherited authentication configuration as a whole;
its fields are not merged. Kerberos requires the optional dependencies and an
available ticket cache. Python clients additionally accept custom `httpx.Auth`
objects, which cannot be represented in YAML. See
[authentication methods](connections.md#authentication-methods) and
[valid and rejected combinations](connections.md#valid-and-rejected-combinations).

## MarkLogic Cloud

Set `cloud` at the root and omit `protocol` and `auth`:

```yaml
app-name: my-app
host: my-org.marklogic.cloud
cloud:
  api-key: my-api-key
  base-path: /ml/my-instance
app-servers:
  - id: manage
    port: 443
  - id: admin
    port: 443
  - id: health
    port: 443
```

Cloud uses HTTPS, port 443 and API-key authentication. API tiers share the gateway
and route through `base-path`. In environment YAML, explicitly replace the
on-premises ports of the predefined Manage, Admin and Health entries with 443;
the default `app-services` entry already resolves to the Cloud port.
| Cloud key | Value | Default |
| --- | --- | --- |
| `api-key` | Gateway API key | Required |
| `base-path` | Gateway route prefix for the instance | Required |
| `token-duration` | Requested token duration in seconds; `0` leaves the gateway default | `0` |

Cloud settings apply to the whole environment. Root credentials, `protocol`,
`auth` and `ssl` do not participate in Cloud resolution; the gateway supplies
its own authentication and HTTPS settings.

## Create an environment in Python

Use [MLEnvironment][mlclient.env.MLEnvironment] to build the same configuration
without a YAML file. `model_validate()` accepts a dictionary with the YAML key
names; nested mappings become the corresponding configuration models:

```python
from mlclient import MLClient
from mlclient.env import MLEnvironment

env = MLEnvironment.model_validate({
    "app-name": "my-app",
    "host": "ml.example.com",
    "username": "app-user",
    "password": "app-password",
    "app-servers": [{"id": "content", "port": 8100, "rest": True}],
})

with MLClient(config=env.provide_config("content")) as ml:
    print(ml.eval.xquery('"Hello World!"'))
```

The same inheritance rules and predefined connections apply. Model attributes
use Python names: `app_name`, `app_servers`, and a server's `identifier`. Input
mappings use `app-name`, `app-servers`, and `id`. To obtain a mapping using YAML
names, call `env.model_dump(by_alias=True)`; this includes credentials,
so treat the result as configuration containing secrets.

A client built from one resolved configuration does not automatically load the
other entries from the environment. For explicit auxiliary configurations:

```python
with MLClient(
    config=env.provide_config("content"),
    manage_config=env.provide_config("manage"),
    admin_config=env.provide_config("admin"),
    health_config=env.provide_config("health"),
) as ml:
    response = ml.manage.databases.get_list()
```

For an existing manager, `manager.config` returns an independent environment
copy. Assign it back to apply changes to subsequently created clients:

```python
from mlclient import MLClientManager
from mlclient.env import MLServerConfig

manager = MLClientManager("local")
env = manager.config
env.app_servers.append(MLServerConfig(id="reporting", port=8110, rest=True))
manager.config = env
```

This changes the manager's in-memory configuration, not the YAML file or clients
already created. The manager constructor still loads a named environment; use
`MLEnvironment` and explicit client configurations for a file-free setup.

## Override settings in Python

Use manager overrides for application-wide defaults and factory overrides for
one client:

```python
from mlclient import MLClientManager

manager = MLClientManager("local", host="gateway.example.com")
with manager.get_client("app-services", port=9100) as ml:
    print(ml.eval.xquery('"Hello World!"'))
```

Precedence is: resolved environment, manager overrides, then factory-call
overrides. Manager overrides apply to every server. Factory overrides apply to
the selected server and its corresponding API; neither the YAML nor subsequent
factory calls are modified.

For example, target a Manage server on another host:

```python
with manager.get_client("manage", host="manage.example.com", port=9002) as ml:
    response = ml.manage.databases.get_list()
```

Here both `ml.http` and `ml.manage` use the selected Manage configuration. Other
API connections retain their environment settings and manager-level overrides.
Auxiliary sessions open on their first request; context exit closes all opened
sessions.

Overrides accept the [HTTPConfig.clone][mlclient.http.HTTPConfig.clone]
parameters: `protocol`, `host`, `port`, `auth`, `username`, `password`, `ssl`,
`cloud`, `retry`, `limits` and `timeout`. Unknown override names raise `TypeError`.

`retry`, `limits` and `timeout` have no environment-YAML counterpart. Their
inheritance and Health-specific defaults are described in
[HTTP configuration](../http-configuration.md), [retries](retries.md), [timeouts](timeouts.md)
and [resource limits](limits.md).

## Load or resolve configuration directly

Use `MLEnvironment.load_file()` when the path is already known:

```python
from mlclient.env import MLEnvironment

env = MLEnvironment.load_file("path/to/mlclient-local.yaml")
config = env.provide_config("app-services")
```

`provide_config()` resolves one server's YAML configuration. To also apply
manager/factory overrides and server-kind HTTP defaults without opening a
connection, use `manager.get_config("app-services", timeout=10)`.

Pass a resolved configuration to `MLClient(config=config)` when building a client
directly. Use `MLClientManager` when auxiliary APIs should also use the environment's
Manage, Admin and Health settings.
