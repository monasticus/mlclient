# MLClient

A Python client and CLI for MarkLogic Server. Start with a query or a document
operation, then choose how much control your application needs.

## Start here

```sh
pip install mlclient
```

```python
from mlclient import MLClient

with MLClient() as ml:
    print(ml.eval.xquery('"Hello World!"'))  # Hello World!
```

This uses the local REST server at `http://localhost:8000` with Digest auth
and `admin` / `admin` credentials. The [quickstart](quickstart.md) explains prerequisites, different
hosts, async usage and CLI setup.

## One library, several ways to work

| Interface | Start with | Go further |
| --- | --- | --- |
| Python | Parsed documents and query results | Sync/async clients, transactions, raw API wrappers and custom endpoints |
| CLI | `ml env init`, `ml eval`, `ml logs` | Import Gradle settings, discover App Servers and select multiple connections |

[The Python guide](user/clients.md) helps choose between `ml.documents`,
`ml.rest.documents` and `ml.http`. [The CLI guide](user/cli.md) gets a project
connected without writing Python. [Recipes](recipes.md) show metadata cleanup,
concurrent evaluations and a custom application API.

## From simple usage to application-specific control

Use [environments](user/environments.md) to share connection settings across scripts and
commands. Configure [authentication and TLS](user/python/connections.md), then
add HTTP retry, timeout and pool limits where the application needs them.
Manage, Admin and Health can have independent connection settings.

For your own application routes, [extend the client](user/python/custom-api.md)
with a Call, an API wrapper and a higher-level method. The
[API reference](reference/mlclient/index.md) is generated from the implementation
and describes all available modules and public signatures.

## An independent alternative

MLClient began roughly eight months before the MarkLogic Python Client and
continued as an independent project after a development break. Its focus includes
async usage, composable client layers and command-line workflows. The
[background page](about.md) explains the motivation and links to the MarkLogic
client as another option.

To help improve the project, read the [contribution guide](contributing.md).
