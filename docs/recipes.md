# Recipes

These examples use stable document and client APIs. Experimental jobs are not
required. Start with a test database and credentials allowed to perform the
operations shown.

## Replace a collection without rewriting content

A data cleanup often changes classification rather than document content.
Read the complete metadata, modify its collection membership, and write a
metadata-only document. Keeping the read and write in a transaction avoids a
separate uncoordinated read/modify/write sequence.

```python
--8<-- "examples/collections.py"
```

Use it with a configured client:

```python
from mlclient import MLClientManager
from collections_recipe import replace_collection

with MLClientManager("local").get_client() as ml:
    changed = replace_collection(ml, "/invoices/42.json", "pending", "processed")
    print(changed)
```

Save the first block as `collections_recipe.py`. The operation preserves content
and other metadata by reading all metadata categories before updating. It returns
`False` when the old collection is absent or the names are equal. A blank new
collection name is rejected before opening a transaction.

A successful context-manager exit commits; an exception rolls back. For a large
migration, use a deliberate batch size and checkpoint strategy rather than one
unbounded transaction. See [document models](user/python/documents.md) and
[transactions](user/python/transactions.md).

## Read a small group of documents concurrently

When independent reads spend time waiting on the server, an async client lets
them overlap. Reuse one client and bound concurrency:

```python
import asyncio

from mlclient import MLClientManager


async def read_documents(uris):
    semaphore = asyncio.Semaphore(4)
    async with MLClientManager("local").get_async_client() as ml:
        async def read_one(uri):
            async with semaphore:
                return await ml.documents.read(uri)

        return await asyncio.gather(*(read_one(uri) for uri in uris))
```

This is for a small, known list: `gather` still creates one task per URI. For
many URIs, prefer the document service's batch/stream interfaces or feed bounded
chunks into this function. A connection-pool limit bounds active connections;
it does not bound the number of tasks or the result list held in memory.

## Put a custom application API behind one method

If scripts repeatedly compose the same raw HTTP calls, give the operation a
name. The [custom API guide](user/python/custom-api.md) builds
`ml.tasks.list()` and `ml.open_task_titles()` on a shared connection, with sync
and async versions. This keeps transport details out of application scripts
while retaining access to the raw response when needed.
