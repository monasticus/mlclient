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
from mlclient import MLClient
from collections_recipe import replace_collection

with MLClient() as ml:
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

## Evaluate queries across databases concurrently

Build a small report of document counts across databases. Each evaluation runs
in a different database context, so these are independent requests that can
overlap. Reuse one async client and allow at most four evaluations at a time:

```python
--8<-- "examples/database_counts.py"
```

Save the block as `database_counts.py`, then run it for databases accessible to
your account:

```python
import asyncio
from database_counts import count_documents

counts = asyncio.run(count_documents(["Documents", "Modules"]))
print(counts)
```

Each query counts the documents visible to the connecting user in that database.
The requests do not share a transaction or a cross-database snapshot. Use this
for independent reporting, not operations that need an atomic result.

One client means one connection pool, so `max_connections` is the concurrency
cap: `gather` schedules every task, but only four requests reach the network at
once and the rest await a free connection. That is why no semaphore is needed
here. For a large list, process bounded batches - pool limits bound in-flight
requests, not the number of scheduled tasks.

To read several documents from the same database, prefer a
[single bulk read](user/python/documents.md#read) with `ml.documents.read(uris)`.

## Cap concurrency across several hosts of one cluster

Pool limits bound a single client. When the work spreads over several hosts,
each host needs its own client and therefore its own pool, so `max_connections`
can no longer bound the total. A shared `asyncio.Semaphore` is the aggregate cap.
Derive each host's client from one resolved configuration with
`HTTPConfig.clone(host=...)`, so credentials, TLS and timeouts stay identical:

```python
--8<-- "examples/cluster_hosts.py"
```

Run one read-only probe on every host:

```python
import asyncio
from cluster_hosts import eval_on_each_host

names = asyncio.run(eval_on_each_host(
    ["node-1.example", "node-2.example", "node-3.example"],
    "xdmp:host-name()",
))
print(names)
```

`AsyncExitStack` closes every client on exit, including on error. The semaphore
caps evaluations in flight across all hosts at once; raise `max_in_flight` to
allow more overlap, or lower it to spare a loaded cluster.

## Put a custom application API behind one method

If scripts repeatedly compose the same raw HTTP calls, give the operation a
name. The [custom API guide](user/python/custom-api.md) builds
`ml.rest.tasks.list()` for the raw response and `ml.tasks.open_titles()` for
parsed Python on a shared connection, with sync and async versions. This keeps
transport details out of application scripts while retaining access to the raw
response when needed.
