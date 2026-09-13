# MLClient

A Python client and CLI for MarkLogic Server. Start with a query or a document
operation, then choose how much control your application needs.

## Start here

```sh
python -m pip install mlclient
```

```python
from getpass import getpass
from mlclient import MLClient

with MLClient(username="my-user", password=getpass("MarkLogic password: ")) as ml:
    print(ml.eval.xquery("1 + 1"))  # 2
```

This connects to an existing REST App Server at `localhost:8000` using your
credentials. The [quickstart](quickstart.md) explains prerequisites, different
hosts, async usage and CLI setup.

## One library, several ways to work

| Interface | Start with | Go further |
| --- | --- | --- |
| Python | Parsed documents and query results | Sync/async clients, transactions, raw API wrappers and custom endpoints |
| CLI | `ml env init`, `ml eval`, `ml logs` | Import Gradle settings, discover App Servers and select multiple connections |
| AI agents | The same Python and CLI interfaces | MCP/skill adapters are planned; they are not bundled in the current package |

[The Python guide](user/pythonapi.md) helps choose between `ml.documents`,
`ml.rest.documents` and `ml.http`. [The CLI guide](user/cli.md) gets a project
connected without writing Python. [Recipes](recipes.md) show metadata cleanup,
concurrent reads and a custom application API.

## From simple usage to application-specific control

Use [environments](user/setup.md) to share connection settings across scripts and
commands. Configure [authentication and TLS](user/python/connections.md), then
add HTTP retry, timeout and pool limits where the application needs them.
Manage, Admin and Health can have independent connection settings.

For your own application routes, [extend the client](user/python/custom-api.md)
with a Call, an API wrapper and a high-level method. The
[API reference](reference/mlclient/index.md) is generated from the implementation
and describes all available modules and public signatures.

## An independent alternative

MLClient began roughly eight months before the MarkLogic Python Client and
continued as an independent project after a development break. Its focus includes
async usage, composable client layers and command-line workflows. The
[background page](about.md) explains the motivation and links to the MarkLogic
client as another option.

From 1.0.0, stable public APIs and commands follow [SemVer](stability.md).
Jobs remain experimental. Broader REST coverage, project-management CLI workflows
and dedicated agent adapters are future directions, not current completeness
claims.

To help improve the project, read the [contribution guide](contributing.md).
