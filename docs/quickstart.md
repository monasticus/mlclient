# Quickstart

MLClient connects Python scripts and command-line tools to MarkLogic Server.
You need a running server, a reachable REST App Server and credentials with
permission for the operation. Installing MLClient does not install MarkLogic.

## Install

```sh
python -m pip install mlclient
```

The library supports Python 3.10–3.14. Use a virtual environment for your project.
For release candidates, explicitly opt in with `python -m pip install --pre mlclient`.

## Run your first query

The default host and REST port are `localhost:8000`. This example asks for a
password rather than storing it in source:

```python
from getpass import getpass

from mlclient import MLClient

with MLClient(username="my-user", password=getpass("MarkLogic password: ")) as ml:
    result = ml.eval.xquery("1 + 1")
    print(result)  # 2
```

Use an account allowed to evaluate code. Set `host` and `port` if your REST
App Server is elsewhere. For an HTTPS server, add `protocol="https"`; see
[connection options](user/python/connections.md) for certificate verification
and authentication details.

The context manager closes the client's connections on exit. Query results are
parsed into Python values; use `ml.rest.eval.post(...)` when you need the raw
HTTP response instead.

## Use async in an async application

```python
import asyncio
from getpass import getpass

from mlclient import AsyncMLClient


async def main(password):
    async with AsyncMLClient(username="my-user", password=password) as ml:
        print(await ml.eval.xquery("1 + 1"))


asyncio.run(main(getpass("MarkLogic password: ")))
```

Inside an existing event loop, await your function instead of calling
`asyncio.run`. Reuse a client across related operations rather than creating a
new connection for every document.

## Prefer the command line?

```sh
ml env init
ml eval -x '1 + 1'
ml version
```

Review the generated local environment and supply your connection settings
before the last two commands. The [CLI guide](user/cli.md) shows importing a
Gradle project's configuration, discovering servers from a host, and choosing
among multiple connections.

Continue with [documents](user/python/documents.md),
[configuration](user/setup.md), or a [complete recipe](recipes.md).
