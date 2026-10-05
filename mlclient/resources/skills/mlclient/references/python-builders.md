# Python query construction and execution

Keep Python orchestration in Python. Use public builders for supported native
functions; keep substantial native modules in separate `.xqy`/`.sjs` files.
No string interpolation of query source, values or names is necessary.

## Three different operations

| Operation | What it does |
| --- | --- |
| `mlclient.functions.xqy.cts/fn/xdmp/xs` | Construct expression trees; no request |
| `ml.eval.expression(expression)` | Compile/bind an expression and execute it |
| `CtsService(ml.rest)` / `AsyncCtsService(ml.rest)` | Execute CTS operations and return service models |

Builders are useful for nested expressions, index references, types and
consistent external binding. Dedicated services are useful when their parsing
and orchestration fit the task. Inspect the installed method's signature before
choosing keyword arguments; a native function's argument names are not always
the Python API's keyword names.

```python
from mlclient import MLClientManager
from mlclient.functions.xqy import cts, fn

async def open_order_values(environment):
    async with MLClientManager(environment).get_async_client() as ml:
        query = cts.and_query([
            cts.collection_query('orders'),
            cts.json_property_value_query('status', 'OPEN'),
        ])
        estimated = await ml.eval.expression(cts.estimate(query))
        reference = cts.json_property_reference('customerId')
        values = await ml.eval.expression(
            cts.values(reference, query=query).pos([1, 20])
        )
        xml_name = fn.qname('urn:orders', 'amount')
        xml_reference = cts.element_reference(xml_name)
        return estimated, values, xml_reference
```

Only use each reference where its range index exists. Returning a builder such
as `xml_reference` does not execute it. A query string passed where a builder
accepts a string can mean **literal data**, not executable XQuery: build
`cts.collection_query('orders')`, not the string `"cts:collection-query(...)"`.

## Paths, sequences and values

Use `xpath('/p:order/p:amount')` for a path and supply the `p` namespace to the
service/`eval.expression`. Paths are validated as extraction/searchable paths;
they are not an escape hatch for arbitrary XQuery. Ordinary strings stay data.
For dynamic expanded names prefer `fn.qname(namespace_uri, local_name)`.
A path reference also needs the database's configured path namespace mapping.

Use `.pos([first, last])` for **one-based inclusive** positions. Python slicing
and native lexicon `skip` have different meanings. Preserve service output types:
`SearchHit` includes source context/content, `ValueHit` includes frequency;
raw expression results follow the eval parser's empty/scalar/list convention.

`expression.compile()` returns source and independent external bindings for
inspection. Let `ml.eval.expression` do compilation/execution in normal code;
do not build an alternative HTTP evaluator just to use builders. Keep model
objects and binary bytes until intentional serialization instead of converting
all results to strings.

## Async implementation choices

- Reuse one open async client per compatible connection context. Use bulk
  document requests before parallelising one request per URI.
- Bound tasks as well as connections. A semaphore around requests does not
  bound millions of already-created tasks; use chunks or a bounded queue.
- Consume generators/batches immediately. `read_stream` is an async iterator in
  async code, but its HTTP response can still be buffered; distinguish parser
  iteration from byte-streaming transport.
- `await AsyncLogsService.get()` returns a normal iterator. Async request does
  not imply async iteration over the resulting in-memory values.
- Await cancellation cleanup before closing clients or files. Attach enough
  input context to failed tasks for retry/reporting, without exposing secrets.
- Use `aiofiles` for sustained local file work; filesystem operations and heavy
  CPU parsing otherwise block the event loop. Use `asyncio.to_thread` for bounded
  synchronous I/O helpers. More async tasks do not accelerate a CPU-bound query.

See [concurrency templates](templates.md), [URI workflows](uri-workflows.md),
[documents](documents.md), [configuration](configuration.md) and
[custom application APIs](extensions.md) for complete operation-specific flows.
