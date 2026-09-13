[![License](https://img.shields.io/github/license/monasticus/mlclient?label=License&style=plastic)](https://github.com/monasticus/mlclient/blob/main/LICENSE)
[![Version](https://img.shields.io/pypi/v/mlclient?color=blue&label=PyPI&style=plastic)](https://pypi.org/project/mlclient/)
[![Python](https://img.shields.io/pypi/pyversions/mlclient?logo=python&label=Python&style=plastic)](https://www.python.org/)
[![Documentation](https://img.shields.io/badge/docs-Material-blue)](https://monasticus.github.io/mlclient/)
[![Build](https://img.shields.io/github/actions/workflow/status/monasticus/mlclient/unit-test.yml?label=Test%20MLClient&style=plastic)](https://github.com/monasticus/mlclient/actions/workflows/unit-test.yml?query=branch%3Amain)
[![Code Coverage](https://img.shields.io/badge/Code%20Coverage-100%25-brightgreen?style=plastic)](https://github.com/monasticus/mlclient/actions/workflows/coverage-badge.yml?query=branch%3Amain)

# MLClient

A Python client and command-line interface for MarkLogic Server. Use parsed
Python values for everyday work, resource wrappers for explicit REST operations,
or raw HTTP for custom application endpoints. Sync and async clients share the
same approach to configuration and connection management.

## Install and connect

```sh
python -m pip install mlclient
```

Python 3.10–3.14 is supported. You need a running MarkLogic REST App Server and
credentials authorized for the operation. The default address is `localhost:8000`.

```python
from getpass import getpass
from mlclient import MLClient

with MLClient(username="my-user", password=getpass("MarkLogic password: ")) as ml:
    print(ml.eval.xquery("1 + 1"))  # 2
```

Start with the [quickstart](https://monasticus.github.io/mlclient/latest/quickstart/)
for async usage and the next steps.

## Choose your level of control

```python
# Alternatives for reading an existing document, inside a client context:
document = ml.documents.read("/example.json")
response = ml.rest.documents.get(uri="/example.json")
response = ml.http.get("/v1/documents", params={"uri": "/example.json"})
```

- Document models, metadata operations, eval and transactions for application code.
- REST, Manage and Admin APIs with explicit routing and raw responses.
- HTTP/HTTPS, TLS client certificates, Cloud and configurable authentication.
- Runtime retry, timeout and pool limits; independent auxiliary connections.
- Public extension points for your application's endpoints and services.

See the [Python guide](https://monasticus.github.io/mlclient/latest/user/pythonapi/)
and [connection options](https://monasticus.github.io/mlclient/latest/user/python/connections/).
Supported wrappers are listed in the generated reference; full REST coverage is
an ongoing goal.

## Use the CLI

```sh
ml env init                            # Create and review project configuration
ml env show                            # Inspect environments
ml eval -x '1 + 1'                      # Evaluate code
ml http get /v1/documents uri=/doc.json # Send a raw request
ml logs -s 8002                        # Read a server's logs
ml log-level                          # Inspect the group log level
ml health                             # Check HealthCheck readiness
ml version                            # Read the server version
```

You can import an ml-gradle configuration or discover App Servers from a host.
Store multiple connections in one environment and select one with
`-c/--connection` where supported. `logs -s/--server` selects logs by identifier
or port; `log-level -s/--server` selects an actual MarkLogic App Server name.
Read the [CLI guide](https://monasticus.github.io/mlclient/latest/user/cli/).

Agents can use the Python API or CLI. MCP and skill adapters are a planned
integration layer; this package does not yet distribute an MCP server or an
end-user skill.

## Background and stability

I started MLClient roughly eight months before the
[MarkLogic Python Client](https://github.com/marklogic/marklogic-python-client),
initially unaware of that project. After a break, I continued to offer another
approach, particularly for async code, layered APIs and CLI workflows. If the
requests-based MarkLogic client fits your needs, it is also worth considering.
More background and future directions are in the
[project notes](https://monasticus.github.io/mlclient/latest/about/).

Starting with 1.0.0, stable public APIs and CLI commands follow SemVer.
`mlclient.jobs` remains explicitly experimental and may change in minor releases.
See the [stability policy](https://monasticus.github.io/mlclient/latest/stability/)
and [release notes](https://github.com/monasticus/mlclient/releases).

MLClient is independently maintained and licensed under MIT. Contributions are
welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).
