# Async support

Use `AsyncMLClient` in asynchronous applications. Its configuration matches
`MLClient`; request operations are awaited.

```python
import asyncio
from mlclient import AsyncMLClient


async def main():
    async with AsyncMLClient() as ml:
        result = await ml.eval.xquery('"Hello World!"')
        print(result)


asyncio.run(main())
```

Inside an existing event loop, await your function instead of calling
`asyncio.run()` again.

## Reuse the client

Keep one client open for related operations so its connections can be reused.
Exit the `async with` block to close all opened connections, including auxiliary
Manage, Admin and Health connections.

```python
async with AsyncMLClient() as ml:
    documents = await ml.documents.read(["/first.json", "/second.json"])
```

## Run independent requests concurrently

Use `asyncio.gather()` for independent evaluations, such as counts in different
database contexts:

```python
async with AsyncMLClient() as ml:
    documents_count, modules_count = await asyncio.gather(
        ml.eval.xquery("fn:count(fn:collection())", database="Documents"),
        ml.eval.xquery("fn:count(fn:collection())", database="Modules"),
    )
```

For more databases, bound concurrency as shown in the
[concurrent eval recipe](../../recipes.md#evaluate-queries-across-databases-concurrently).
For multiple documents in one database, use the bulk read shown above.
[Pool limits](limits.md) control active connections, not how many tasks you create.

## Use an environment

```python
from mlclient import MLClientManager

async with MLClientManager("local").get_async_client() as ml:
    result = await ml.eval.xquery('"Hello World!"')
```

The manager applies the same [configuration overrides](../http-configuration.md) to sync
and async clients. Raw API wrappers are available as `ml.rest`, `ml.manage` and
`ml.admin`; their request methods are awaited too.

## API differences

Most operations mirror the synchronous API. Two lifecycle differences are worth
calling out:

- Use `await ml.version()` to resolve the server version; the synchronous client
  exposes a cached `ml.version` property.
- Opening a transaction performs I/O, so use `async with await ml.transaction()`.

See [transactions](transactions.md) and the generated
[AsyncMLClient reference][mlclient.AsyncMLClient]
for complete signatures. Check the reference when choosing a service: the
standalone `LogLevelService` currently has a synchronous interface.
