# Adaptable templates

Copy the smallest relevant asset into the user's project; replace environment,
connection, collection and database values explicitly. These are functions to
call from a script, not programs that silently run against an assumed server.

| Template | When to use | Call |
| --- | --- | --- |
| [concurrent_eval.py](../assets/concurrent_eval.py) | Independent queries across databases, Python 3.10+ | `await evaluate('dev', 'content', databases, query_file, concurrency=8)` |
| [export_documents.py](../assets/export_documents.py) | Bounded export of known URIs including metadata | `await export('dev', 'content', uris, './export')` |
| [custom_api.py](../assets/custom_api.py) | Repeated custom endpoint with sync/async clients | `ml.rest.my_awesome_endpoint()` / awaited equivalent |
| [uri_pages.py](../assets/uri_pages.py) | Bounded native URI cursor batches; pure Python builders | `async for page in uri_pages(ml, query, batch_size=1000)` |
| [forest_partitions.xqy](../assets/forest_partitions.xqy) | Capture target database primary-forest scopes for privileged host workers | `await ml.eval.file(path, database=database)` |
| [search_page.xqy](../assets/search_page.xqy) | Filtered stable URI page without relying on URI lexicon | `ml eval search_page.xqy --var collection=products --var start=1 --var size=25` |

At a standalone entry point, call async functions via `asyncio.run(main())`.
Within an existing event loop, await them. Bound overall deadlines with
`asyncio.wait_for` if needed. The bounded eval template cancels and awaits every
pending sibling before closing the client. Chunking bounds both task count and
connections; larger documents also need a byte budget.

Use [documents](documents.md) for bulk writes and transactions,
[search](search.md) for index reference construction/aggregates, and
[configuration](configuration.md) for transport policy. Do not replace an
existing project abstraction solely to match these examples.
