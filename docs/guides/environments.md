# Environments

An environment stores a project's connection settings in a YAML file. Use the
same file from Python and the CLI, without repeating credentials in each script.

## Create an environment

Save this as `.mlclient/mlclient-local.yaml` in your project:

```yaml
--8<-- "guides/environments/mlclient-local.yaml"
```

This describes a local MarkLogic server with Digest authentication and one REST
connection named `content` on a custom port. Set the host, credentials and port
to match your server. `app-name` labels the application; `id` is the name you
select the connection by, and `rest: true` makes it eligible as the default REST
connection.

[Download this example](environments/mlclient-local.yaml), or create the basic
local configuration and edit it to add your App Server:

```sh
ml env init local
ml env edit local
```

See [`ml env init`](../cli/env/init.md) and [`ml env edit`](../cli/env/edit.md).

## Use it from Python

`MLClientManager("local")` loads the file and creates clients from its settings.
Select a connection by the `id` from the YAML:

```python
from mlclient import MLClientManager

manager = MLClientManager("local")
with manager.get_client("content") as ml:
    print(ml.eval.xquery('"Hello World!"'))
```

The manager searches for `.mlclient` in the current directory and its parents,
so the same code works from a project subdirectory.

Omit the identifier to select the first connection marked `rest: true` - here,
`content`:

```python
with manager.get_client() as ml:
    print(ml.eval.xquery('"Hello World!"'))
```

### Choose a client

Reuse the manager to create clients for different tasks. Each factory call creates
a separate client; leaving its `with` block closes that client, and the manager
remains available for later calls.

| Factory | Returns | Use it for |
| --- | --- | --- |
| [`get_client()`][mlclient.MLClientManager.get_client] | [`MLClient`][mlclient.MLClient] | Services and API wrappers; omit the identifier for the first REST connection |
| [`get_async_client()`][mlclient.MLClientManager.get_async_client] | [`AsyncMLClient`][mlclient.AsyncMLClient] | The same operations with `await`; also defaults to the first REST connection |
| [`get_http_client(id)`][mlclient.MLClientManager.get_http_client] | [`HttpClient`][mlclient.clients.HttpClient] | Raw HTTP requests to one connection |
| [`get_async_http_client(id)`][mlclient.MLClientManager.get_async_http_client] | [`AsyncHttpClient`][mlclient.clients.AsyncHttpClient] | Raw HTTP requests with `await` |
| [`get_config(id)`][mlclient.MLClientManager.get_config] | [`HTTPConfig`][mlclient.http.HTTPConfig] | Resolve settings without creating a client or opening a connection |

The predefined `app-services`, `manage`, `admin` and `health` connections are
always available, even when the YAML file does not list them. For example,
use the same manager for a raw Manage request and an async search:

```python
with manager.get_http_client("manage") as http:
    response = http.get("/manage/v2/databases", params={"format": "json"})
    response.raise_for_status()

async def find_documents():
    async with manager.get_async_client() as ml:
        return await ml.search.documents("coffee")
```

For configuration alone:

```python
config = manager.get_config("content")
```

See [async support](async.md) for running async code and
[more on environments](../advanced/more-on-environments.md) for configuration overrides.

## Use it from the CLI

Commands use `local` by default:

```sh
ml env show local
ml eval -x '"Hello World!"'
ml logs
```

[`ml env show`](../cli/env/show.md) displays the file's settings and masks secrets.

## Add another environment

Create `.mlclient/mlclient-dev.yaml` for a development server and change the
settings that differ, such as `host` and credentials. Each file is independent;
`dev` does not inherit settings from `local`.

```python
manager = MLClientManager("dev")
with manager.get_client() as ml:
    print(ml.eval.xquery('"Hello World!"'))
```

Select the same environment in the CLI with `-e`:

```sh
ml eval -e dev -x '"Hello World!"'
```

## Add another connection

A single environment can contain several App Servers. For example, extend the
`app-servers` list with a second REST connection:

```yaml
app-servers:
  - id: content
    port: 8100
    rest: true
  - id: reporting
    port: 8110
    rest: true
```

Both use the file's host and credentials. Select `reporting` in Python or with
the CLI's connection option:

```python
with MLClientManager("local").get_client("reporting") as ml:
    print(ml.eval.xquery('"Hello World!"'))
```

```sh
ml eval -c reporting -x '"Hello World!"'
```

Manage, Admin and Health connections are provided automatically with their
default ports; you do not need to list them for a standard local setup.

## Go further

[More on environments](../advanced/more-on-environments.md) covers per-server
overrides, inheritance, TLS, authentication, Cloud and temporary Python overrides.
For supported transport/authentication combinations and their requirements, see
[connections and authentication](../advanced/connections.md).

Retry, timeouts and pool limits are Python-only HTTP settings. Configure them
through the client or manager as described in [HTTP configuration](../advanced/http/index.md).
