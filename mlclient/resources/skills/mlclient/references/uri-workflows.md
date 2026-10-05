# URI selection and large exports

## Decide from the task and an estimate

1. Compose a CTS query, checking its indexes and fragment scope.
2. Use `cts:estimate` / a Python builder estimate for approximate size. It counts
   candidate fragments, not necessarily distinct URIs or exact matching documents.
3. For a modest result, use one native URI call with a positional cap. Do not
   materialize documents just to obtain their URIs.
4. For many results, use cursor batches and write incrementally to a file.
5. For millions, consider privileged host workers with fixed forest partitions.
   Use a normal serial cursor when topology privileges or direct host routing
   are unavailable. There is no universally correct count threshold: consider
   URI length, response size, latency and available resources.

`cts:uris` requires the URI lexicon. It returns index candidates; it does not
filter loaded documents and does not accept the `filtered` search option. For
exact matches when index resolution can overmatch, use filtered document search
and extract URIs intentionally as a different, more expensive operation. Do
not silently substitute that path or automatically enable an index.

## Python: builders, not embedded XQuery

```python
from mlclient.functions.xqy import cts

query = cts.and_query([
    cts.collection_query('orders'),
    cts.json_property_value_query('status', 'OPEN'),
])
estimate = await ml.eval.expression(cts.estimate(query))
uris = await ml.eval.expression(
    cts.uris(query=query, options=['document', 'item-order', 'ascending'])
       .pos([1, 1000])
)
```

A singleton result is a string; several items are a list, and an empty sequence
is `[]`. Normalize only where your workflow needs a list.

## Cursor: inclusive start plus one lookahead

Use [uri_pages.py](../assets/uri_pages.py) for this exact algorithm:

- First `start` is the empty string.
- Read `cts.uris(start=cursor, ...).pos([1, batch_size + 1])`.
- Emit the first `batch_size` entries.
- If there is a lookahead entry, use that **unemitted** URI as the next `start`.
  The native start is inclusive, so the next page emits it normally.
- If there is no lookahead, finish. Keep query/options/forest scope unchanged.

Do not use native `limit=N`, `skip=N`, ever-growing offsets, or drop the first
entry unconditionally. The boundary URI can disappear between live requests;
`cts:uris` starts at its successor if it is no longer present. Emitting the
lookahead now and again on the next page would duplicate it; advancing past it
without emitting it would lose it.

The template is an async generator of batches. Consume and release each batch;
`list(...)`, collecting all batches or creating a task for every URI defeats the
memory bound. The client still buffers each HTTP response, so choose batch size
with a byte budget, not just item count.

## Privileged host workers: proposed flow

1. Discover hosts and **primary forests of the target database**. The separate
   [forest_partitions.xqy](../assets/forest_partitions.xqy) file uses
   `xdmp:hosts`, `xdmp:database-forests(..., false())` and `xdmp:host-forests`.
   Run with `await ml.eval.file(path, database=database)`; do not embed its source
   in Python. Manage API discovery is another route when already available.
2. Capture topology once. Validate that partitions are nonempty, disjoint and
   cover the intended attached primary forests. Exclude replicas; host forests
   belonging to another database must not enter the export. **An empty forest
   sequence means all database forests**, so never launch an empty partition.
3. Start one worker per host, with an `asyncio.Semaphore` bounding active workers.
   Each worker retains its original forest-ID list for every cursor request.
4. Use a reachable App Server on that host with the intended database binding.
   A manager client can override `host` while retaining configured auth/TLS/port;
   configured host names may need an address mapping. Verify that the server
   exists on each host and that proxies do not route every request to one node.
   Forest scope alone does not guarantee local evaluation through a load balancer.
5. Each worker consumes `uri_pages(..., forest_ids=its_fixed_ids)` and immediately
   writes batches with `aiofiles`. Prefer separate staging files per host;
   alternatively serialize writes to one shared file with an async lock.
6. Cancel and await all siblings on failure **before** closing files/clients.
   Retain a failure/partial status instead of reporting complete output. Publish
   final files atomically only after successful completion; protect existing
   outputs. JSONL string values safely encode unusual characters in URI strings.

Per-host files are ascending within their scope. Concatenation is not global
sorting; use an external merge if global order is required. Record actual count,
query/database, original forest scopes and each host's cursor for resumability.
Estimates are planning hints, not completion proof. Repeated requests read live
data: concurrent writes, rebalancing or failover can change the result set.
For a reproducible export, freeze relevant changes or deliberately implement a
supported snapshot strategy; a single timestamp is not automatically valid
across arbitrary forests/requests or credentials.

Native reference: [cts:uris](https://docs.marklogic.com/cts:uris).
