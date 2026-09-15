# Search

!!! warning "Experimental API"
    The search builders and their services are experimental and outside the
    stable API contract. They may change incompatibly in minor releases. The
    surface is complete enough for real use - this notice is about stability,
    not readiness.

I wanted a way to search from this library. MarkLogic exposes a REST search
endpoint, but in day-to-day development what has always worked best for me is
building queries out of `cts:` functions directly. And since I consider this
library a good fit for both simple lookups and more involved queries, I decided
to mirror that `cts:` API in Python rather than wrap the search endpoint.

Two things fall out of that choice. You do not have to learn another query API -
if you know `cts:and-query` and `cts:element-range-query`, you already know
this. And you never mix strings of inline XQuery into your Python: a query is an
object graph, so there are no quoting rules to get wrong and nothing to
concatenate by hand.

## Building a query

Import the namespaces you need. Each mirrors an XQuery prefix: `cts`, `fn`,
`xdmp` and `xs`.

```python
from mlclient.functions import cts, xs

query = cts.and_query((
    cts.directory_query("/reactions/", "infinity"),
    cts.element_range_query(xs.qname("yield"), ">=", 80),
))
```

A builder returns an expression tree; it performs no I/O. Nest builders exactly
as you would nest `cts:` calls in XQuery. Values you pass - a directory URI, a
yield threshold - are never interpolated into the query text: they travel to
MarkLogic as external variables, so a value like `'); xdmp:document-delete("`
is just a string, never executable.

`xs` constructors give a value an explicit type. Plain Python values are typed
by inference (`int` becomes `xs:integer`, a `datetime.date` becomes `xs:date`),
so reach for `xs` only when you need to override that - for example forcing a
whole number to `xs:double`.

## Running it

A builder namespace on its own does not touch the server. To execute, use the
matching service, which inherits the exact same builder API and adds the
executing calls - `search`, `uris`, `values`, `estimate`:

```python
from mlclient import MLClient
from mlclient.functions import cts, xs
from mlclient.services import CtsService

with MLClient() as ml:
    search = CtsService(ml.rest)
    query = cts.element_range_query(xs.qname("yield"), ">=", 80)
    hits = search.search("/reaction", query, range=10)
```

The service compiles the tree once and evaluates it through `/v1/eval`. `range`
is optional and slices the result lazily in XQuery style: `10` returns the first
ten hits, `(11, 20)` the next ten. Because the slice is a `[lo to hi]` predicate,
MarkLogic stops early instead of materialising every match.

[CtsService][mlclient.services.CtsService] targets MarkLogic 12 by default and
verifies version-gated functions before evaluating - passing `version="11.0"`
rejects, for instance, `cts:document-root-query` on a server too old to have it.

## Composing across namespaces

Because every builder returns the same expression type, one namespace nests
inside another. Wrap a `cts:` query in `fn:count` to size a result set, or in
`xdmp:exists` for an index-resolved existence check, in a single round-trip:

```python
from mlclient import MLClient
from mlclient.functions import cts
from mlclient.services import FnService, XdmpService

with MLClient() as ml:
    matches = FnService(ml.rest).count(cts.values(cts.element_reference("mf")))
    present = XdmpService(ml.rest).exists(cts.search("/reaction", cts.true_query()))
```

[FnService][mlclient.services.FnService] and
[XdmpService][mlclient.services.XdmpService] follow the same pattern as
`CtsService`: they inherit the builder namespace and execute what you nest.

## Async

Every service has an async twin - [AsyncCtsService][mlclient.services.AsyncCtsService],
[AsyncFnService][mlclient.services.AsyncFnService] and
[AsyncXdmpService][mlclient.services.AsyncXdmpService] - with the same methods
awaited. See [Async support](async.md).
