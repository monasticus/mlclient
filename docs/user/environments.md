# Environments

An environment stores a project's connection settings in a YAML file. Use the
same file from Python and the CLI, without repeating credentials in each script.

## Create an environment

Save this as `.mlclient/mlclient-local.yaml` in your project:

```yaml
--8<-- "user/environments/mlclient-local.yaml"
```

This describes a local MarkLogic server with Digest authentication and one REST
connection named `content` on a custom port. Set the host, credentials and port
to match your server. `app-name` labels the application; `id` is the name you
select the connection by, and `rest: true` makes it eligible as the default REST
connection.

[Download this example](environments/mlclient-local.yaml), or use
[`ml env init`](cli/env/init.md) to create a file interactively.

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

The predefined `app-services`, `manage`, `admin` and `health` connections are
always available even when the file does not list them, so you can select one by
id without declaring it:

```python
with manager.get_client("app-services") as ml:
    print(ml.eval.xquery('"Hello World!"'))
```

Use `get_async_client()` in async code; see [async support](python/async.md).
Leaving the client context closes its opened connections.

## Use it from the CLI

Commands use `local` by default:

```sh
ml env show local
ml eval -x '"Hello World!"'
ml logs
```

[`ml env show`](cli/env/show.md) displays the file's settings and masks secrets.

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

[More on environments](python/more-on-environments.md) covers per-server
overrides, inheritance, TLS, authentication, Cloud and temporary Python overrides.
For supported transport/authentication combinations and their requirements, see
[connections and authentication](python/connections.md).

Retry, timeouts and pool limits are Python-only HTTP settings. Configure them
through the client or manager as described in [HTTP configuration](http-configuration.md).
