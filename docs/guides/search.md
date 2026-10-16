# Search

MLClient has two search services:

| Service | Access | Runs through | Required privileges |
| --- | --- | --- | --- |
| REST search | `ml.search` | `/v1/search`, `/v1/values` | `rest-reader`; `xdmp-eval-in` for another database |
| CTS search | `CtsService(ml.rest)` | `/v1/eval` with generated XQuery | eval privileges such as `xdmp-eval` |

Use `ml.search` by default. It sends structured, CTS or string queries to the
REST Search API, returns mlclient models and never evaluates code, so it works
for REST users without eval privileges, which production servers usually
withhold. Searching a database other than the REST server's own, with
`ml.search(database=...)`, also needs the `xdmp-eval-in` privilege, as for
every REST request with a `database` parameter. REST search reports also
include relevance scores, facets and metrics.
Use [CtsService](#cts-search-with-eval) for searching XML subtrees or composing
native XQuery operations in one request.

## Choose a query

Every operation accepts the same query argument:

| Query | Sent as |
| --- | --- |
| A CTS query from [`cts`][mlclient.xquery.Cts], or a JSON dictionary `{"ctsquery": {...}}` | Serialized CTS JSON, `{"ctsquery": ...}` |
| A structured query from [`sq`][mlclient.search.structured.StructuredQueryBuilder] or its classes, or a JSON dictionary `{"query": {...}}` | Serialized structured JSON, `{"query": ...}` |
| A JSON combined-query dictionary, `{"search": {...}}` | Combined query including inline options and/or `qtext` |
| A string, such as `"coffee AND tea"` | Search API string query (`qtext`) |
| `None` (default) | No query; matches every document |

For lexicon operations (`values`, `tuples`, `aggregate`), use a CTS query object
instead of raw CTS JSON; see the [lexicon restriction](../advanced/queries.md#combined-queries-with-options-and-text).

```python
from mlclient import MLClient
from mlclient.xquery import cts
from mlclient.search.structured import sq

with MLClient() as ml:
    by_cts = ml.search.documents(
        cts.and_query([cts.collection_query("products"), cts.word_query("coffee")]),
    )
    by_structure = ml.search.documents(
        sq.and_(sq.collection("products"), sq.term("coffee")),
    )
    by_text = ml.search.documents("coffee AND tea")
```

You can also supply native JSON as a Python dictionary, using the same scope
settings as for query objects. A JSON-encoded string remains a text query:

```python
with MLClient() as ml:
    by_structure = ml.search.documents(
        {"query": {"term-query": {"text": "coffee"}}},
    )
    by_cts = ml.search.documents(
        {"ctsquery": {"wordQuery": {"text": "coffee"}}},
    )
    by_combined = ml.search.documents(
        {
            "search": {
                "query": {"term-query": {"text": "coffee"}},
                "options": {"page-length": 20},
            },
        }
    )
```

For query construction, see [Structured and CTS queries](../advanced/queries.md),
including the [structured builder](../advanced/queries.md#builder) and
[CTS constructors](../advanced/queries.md#cts-queries).

Both vocabularies compose with `&` (and), `|` (or) and `~` (not). Chained
operators build one flat query, so the following are equivalent:

```python
coffee_not_decaf = (
    cts.collection_query("products")
    & cts.word_query("coffee")
    & ~cts.word_query("decaf")
)
same_query = cts.and_query(
    [
        cts.collection_query("products"),
        cts.word_query("coffee"),
        cts.not_query(cts.word_query("decaf")),
    ],
)
structured = sq.collection("products") & sq.term("coffee") & ~sq.term("decaf")
```

## Find documents

`documents()` performs a multi-document read and returns
[Document][mlclient.models.Document] models in search result order: [`XMLDocument`][mlclient.models.XMLDocument],
[`JSONDocument`][mlclient.models.JSONDocument], [`TextDocument`][mlclient.models.TextDocument] or [`BinaryDocument`][mlclient.models.BinaryDocument]. MarkLogic sends only the
documents - no search report, snippets or facets - and an empty list means
nothing matched.

```python
with MLClient() as ml:
    first_page = ml.search.documents("coffee", pos=[1, 10])
    with_collections = ml.search.documents(
        "coffee",
        pos=1,
        category=["content", "collections"],
    )
    print(with_collections[0].metadata.collections())
```

`pos` takes a one-based position or an inclusive `[start, end]` range. Without
`pos` you get the first page only: the `page-length` of inline options, else
**10**. A multi-document read ignores the `page-length` of installed options, so
pass `pos` with them. Pass a range to read more, for example `pos=[1, 1000]`. `category`
accepts the same values as [document reads](documents.md); include `content` to
keep the document content.

## Get URIs

`uris()` returns the URIs of matching documents as strings, in the same order and
with the same paging as `documents()` - the first 10 without `pos`:

```python
with MLClient() as ml:
    uris = ml.search.uris(cts.collection_query("products"), pos=[1, 100])
```

The service requests the smallest metadata category for each match and reads the
URI from each part's header, so no document content crosses the network.

## Read lexicon values

`values()` reads a values definition from named or inline query options and returns
[ValueHit][mlclient.models.ValueHit] objects. Each value is converted from the type
MarkLogic reports, such as `Decimal` for `xs:decimal` or `date` for `xs:date`.

```python
with MLClient() as ml:
    products = ml.search(options="product-options")
    prices = products.values("price", cts.collection_query("products"), pos=[1, 20])
    for hit in prices:
        print(hit.value, hit.frequency)
```

The `product-options` options must define a `values` entry named `price` backed
by a range index. Unlike documents and URIs, without `pos` every selected value is
returned, as `/v1/values` does. `direction`
chooses ascending or descending order; `frequency="item"` counts occurrences,
while `frequency="fragment"` counts matching fragments. `limit` caps the lexicon
subset **before** `pos` selects a page.

Tuples definitions raise `ValueError` in `values()`; use `tuples()` instead.

## Aggregate values

`aggregate(name, function, query=None, ...)` applies an aggregate to a
values or tuples definition. It returns the parsed result, not a [`ValueHit`][mlclient.models.ValueHit]:

```python
options = opt.options(opt.values("price", Range(Element("price"), "xs:decimal")))

with MLClient() as ml:
    prices = ml.search(options=options)
    total_price = prices.aggregate("price", "sum")
    average_price = prices.aggregate("price", "avg")
    price_count = prices.aggregate("price", "count")
```

`count` returns an integer, decimal sums and averages retain `Decimal`, and
statistical aggregates return floats. An empty aggregate result is returned as
`None` (for example, an average with no matching values). Supported built-ins include min, max, median,
standard deviation, variance, correlation and covariance; binary statistics use
tuples.
For a native plugin already installed on MarkLogic, pass its function name and
library path:

```python
with MLClient() as ml:
    result = ml.search(options=options).aggregate(
        "price",
        "customAverage",
        aggregate_path="/native/statistics",
    )
```

A non-empty `aggregate_path` selects a plugin. Its first returned aggregate value
retains its JSON type; the service does not infer the plugin result type from
the lexicon. A missing value returns `None`.
## Read co-occurrences

```python
options = opt.options(
    opt.tuples(
        "price-day",
        Range(Element("price"), "xs:decimal"),
        Range(Element("day"), "xs:date"),
    )
)

with MLClient() as ml:
    for hit in ml.search(options=options).tuples("price-day"):
        price, day = hit.values
        print(price, day, hit.frequency)
```

[TupleHit][mlclient.models.TupleHit] preserves index order and converts each
component using its own XML Schema type. The service requests XML responses:
MarkLogic rounds decimal tuple values in JSON, whereas XML retains their exact
lexical values. Query and inline options are still sent as JSON. Direction,
frequency, limit and positional paging have the same semantics as `values()`.

## Search reports and snapshot pagination

`report()` returns a [SearchReport][mlclient.models.SearchReport], containing
native JSON result entries (including URI, score and snippets), facets, metrics
and the estimated total. These snippets are **not** whole [`Document`][mlclient.models.Document] objects;
use `documents()` or `documents_with_report()` to read actual content.

```python
with MLClient() as ml:
    products = ml.search(options=options)
    first = products.report("coffee", pos=[1, 10])
    for result in first.results:
        print(result["uri"], result["score"])
    print(first.total, first.facets, first.metrics)
    snapshot = products(timestamp=first.effective_timestamp)
    next_page = snapshot.report("coffee", pos=[11, 20])
```

Reuse the same criteria and `effective_timestamp` for a stable snapshot; the
server must retain that point-in-time version. `view` selects all, results,
facets or metadata. `report.response` retains the complete native JSON report,
including any extra fields requested through query options.

### Documents and report together

`documents_with_report()` returns `tuple[SearchReport, list[Document]]` in that
order, using one multipart request with `view=all`:

```python
with MLClient() as ml:
    products = ml.search(collection="products", options=options)
    report, documents = products.documents_with_report("coffee", pos=[1, 10])
    print(report.total, report.facets)
    for document in documents:
        print(document.uri, document.content)
```

See [Find documents](#find-documents) and
[Search reports](#search-reports-and-snapshot-pagination) for document categories,
paging and report contents.

## Build query options

Pass an installed options name, an inline dictionary, or an immutable
[SearchOptions][mlclient.search.options.SearchOptions] composition to `ml.search`.
The stateless [opt][mlclient.search.options.SearchOptionsBuilder] factories work
like [sq][mlclient.search.structured.StructuredQueryBuilder]: nest typed
components in `opt.options(...)`.

```python
from mlclient.search.options import opt
from mlclient.search.structured import sq

price = opt.range(sq.element("price"), "xs:decimal")
options = opt.options(
    opt.values("price", price),
    opt.range_constraint("price", price),
    opt.sort(price, direction="descending"),
    opt.page_length(20),
    opt.return_facets(False),
)

with MLClient() as ml:
    priced_products = ml.search(collection="products", options=options)
    documents = priced_products.documents("price GT 10", pos=[1, 10])
```

Components and groups are immutable and reusable. Each factory has a typed
constructor signature, so editors suggest its parameters. `opt.options` creates
a complete options object; it never changes a component or another group.
Indexes must already exist in the target database; options do not create them.
See [Search options](../advanced/queries.md#search-options) for reuse, direct
classes and native definitions, and the
[factory reference][mlclient.search.options.SearchOptionsBuilder] for all constructors.

For inline dictionaries, pass the options members directly, without the outer
`{"options": ...}` wrapper:

```python
with MLClient() as ml:
    search = ml.search(options={"page-length": 20})
    documents = search.documents("coffee")
```

### Combine a query, options and text

Call `to_combined_query(options=..., qtext=...)` on a structured or CTS query
and pass the result to a search operation:

```python
combined = sq.collection("products").to_combined_query(
    options={"page-length": 20},
    qtext="coffee",
)

with MLClient() as ml:
    documents = ml.search.documents(combined)
```

The collection filter and text query are AND-related. Options in the combined
query override matching service options; options in a per-operation scope
override both. Other inline option members are retained.
See [Combined queries](../advanced/queries.md#combined-queries-with-options-and-text)
for builders, merging rules and the raw CTS JSON limitation on lexicon operations.

## Scope: databases, filters and options

Where a search runs and which options it uses is its
[SearchScope][mlclient.services.SearchScope]: `database`, `txid`, `collection`,
`directory`, `forest_name`, `options` and `timestamp`. Set it for a series
of searches or override it for one request:

- **For a series of searches**, call the service: `ml.search(database="catalog",
  collection="products")` returns a new service bound to that scope. It sends no
  request and leaves `ml.search` unchanged; calling a scoped service narrows it
  further.
- **For one request**, use `database=` and `txid=` as keyword arguments when
  you only need these basic scope parameters. This also supports `**txn`.
  For more settings, pass `scope=SearchScope(...)`.

At service level all scope settings are keyword arguments, as in
`ml.search(database="catalog", collection="products", options=options)`.
On an operation, direct `database=` and `txid=` override `scope=`, which in turn
overrides the service's defaults.

An omitted field is inherited; `None` clears an inherited value.

```python
from mlclient.services import SearchScope

with MLClient() as ml:
    catalog = ml.search(database="catalog", collection="products", options=options)
    coffee = catalog.documents("coffee", pos=[1, 20])
    archived = catalog.uris("coffee", scope=SearchScope(collection="archive"))
    everywhere = catalog.uris("coffee", scope=SearchScope(collection=None))

    with ml.transaction(database="catalog") as txn:
        pending = catalog.uris("coffee", **txn)
```

`documents()` and `report()` also accept `transform` and `transform_params`: an
installed transform must preserve the native result contract of that operation.
Every operation accepts `timeout`. MarkLogic errors, such as an unknown values
name or a missing index, raise [`MarkLogicError`][mlclient.exceptions.MarkLogicError].

For anything the service does not wrap, call the endpoints directly through
`ml.rest.search` (`get`, `post`, `delete`) and `ml.rest.values` (`get_list`,
`get`, `post`). `ml.rest.search.delete()` removes the documents of a collection or
directory; clearing a whole database requires `clear_database=True`. Those methods return raw [`httpx.Response`](https://www.python-httpx.org/api/#response) objects and accept every
documented parameter of these search/values endpoints, including combined-query
POST bodies, native-plugin aggregates and all native response views. Calls/API
leave raw response headers available, including the effective timestamp.

## Async search

```python
from mlclient import AsyncMLClient


async def find_products():
    async with AsyncMLClient() as ml:
        return await ml.search.uris("coffee", pos=[1, 10])
```

## CTS search with eval

[`CtsService`][mlclient.services.CtsService] mirrors native `cts:` functions and runs them through `/v1/eval`.
It is more flexible than `ml.search` - every search, lexicon and aggregate
function, scored [`SearchHit`][mlclient.models.SearchHit] results, subtree search and composition with other
XQuery builders - but each call evaluates generated XQuery, so the REST user
needs eval privileges.

```python
from mlclient import MLClient
from mlclient.services import CtsService

with MLClient() as ml:
    cts = CtsService(ml.rest)
    hits = cts.search(
        query=cts.and_query(
            [
                cts.collection_query("products"),
                cts.word_query("coffee"),
            ]
        ),
        pos=[1, 10],
    )
    for hit in hits:
        print(hit.source_uri, hit.score, hit.content)
```

The same CTS query objects work in both services: `ml.search.documents(query)`
runs a serializable query over REST, while `CtsService.search(query=query)`
returns scored hits.

`search()` always returns a list of [SearchHit][mlclient.models.SearchHit]
objects, or `[]` for no matches. Query constructors such as
`word_query()` and `and_query()` only build a query; `search()` executes it.

Each hit contains:

- `content`: the parsed result, ready to use.
- `score`: the search relevance score.
- `source_uri`: the source document URI, or `None` if unavailable.
- `source_path`: the location of the returned node; `/` when the server omits it.

JSON objects become dictionaries and arrays become lists. XML documents become
`ElementTree` objects, XML elements become `Element` objects, text becomes `str`,
and binary content stays `bytes`. A search can return mixed types. A JSON array
is held inside a hit's `content`, so it is not confused with the list of hits.

### Select results

Pass `pos=1` to select the first result, `pos=[1, 10]` for the first ten, or
`pos=[11, 20]` for the next ten. Positions are one-based, both range endpoints
are included, and selection happens on the server.

```python
with MLClient() as ml:
    cts = CtsService(ml.rest)
    hits = cts.search(query=cts.collection_query("products"), pos=1)
    if hits:
        print(hits[0].content)
```

Without `pos`, CTS search returns every match; REST search returns its first page.
A selected position returns a one-item list; a missing position returns `[]`.
A two-item list or tuple selects an inclusive range.
Use an explicit ordering option when your application needs stable page ordering;
see [XQuery API: selection and ordering](../advanced/xquery-api.md#selection-and-ordering).

### Work with XML

There are three places to select XML nodes. The first two run in MarkLogic;
the third runs locally in Python:

| Selection | Where | What it changes |
| --- | --- | --- |
| `search(expression=...)` | XQuery, inside `cts:search` | Which candidate nodes are searched and filtered against `query` |
| `search(xpath=...)` | XQuery, after search and `pos` | Which parts of each matching node are sent back |
| `hit.xpath(...)` | Python, after retrieval | Which elements you access in the already returned XML tree |

#### Choose what to search with expression

By default, `expression="/"` searches document nodes. Use an element path to
search smaller subtrees instead. For example, a catalog might contain several
products, only one of which mentions coffee:

```xml
<catalog xmlns="https://monasticus.com/mlclient/examples/products">
  <product><title>Coffee beans</title><price>12</price></product>
  <product><title>Tea leaves</title><price>8</price></product>
</catalog>
```

```python
with MLClient() as ml:
    cts = CtsService(
        ml.rest, namespaces={"p": "https://monasticus.com/mlclient/examples/products"}
    )
    products = cts.search(
        expression="/p:catalog/p:product",
        query=cts.word_query("coffee"),
        pos=[1, 10],
    )
```

With the default filtered search, the query is checked against each selected
product subtree: the coffee product matches, not its tea sibling. Searching
`expression="/"` instead returns the entire matching catalog document, including
both products. This is a change to the search scope, not just the output shape.
Fragment-level constraints such as collection membership still apply to the
containing document. Do not use `unfiltered` when you rely on subtree filtering.

#### Return less XML with search xpath

Pass `xpath` to the search call when you only need part of each matching product:

```python
with MLClient() as ml:
    cts = CtsService(
        ml.rest, namespaces={"p": "https://monasticus.com/mlclient/examples/products"}
    )
    titles = cts.search(
        expression="/p:catalog/p:product",
        query=cts.word_query("coffee"),
        xpath="p:title",
        pos=[1, 10],
    )
```

MarkLogic searches products, selects up to ten hits, then extracts their titles.
Only titles cross the network, reducing response size and client parsing work;
this does not necessarily make the underlying search faster. The product's price
and other siblings are not in the response.

The path is relative to each hit. With the default document-node expression,
use `xpath="p:catalog/p:product/p:title"` instead. A leading `/` starts at the
hit's document root, not at the selected subtree. `xpath=None` returns hits
unchanged. Each extracted node retains its original hit's score and hit order.
One hit can produce zero or several nodes, so the result count can differ from
the selected range size.

Both server paths use MarkLogic's restricted, searchable/extraction XPath syntax,
not arbitrary XQuery or Python's XPath subset. Invalid paths raise
[`MarkLogicError`][mlclient.exceptions.MarkLogicError] with code `MLCLIENT-INVALID-PATH`; empty paths are rejected
locally. For example, `/fn:string()` is not an extraction path. Native search
can nevertheless return text and JSON scalar nodes as well as XML/JSON trees.
See [namespace bindings](../advanced/xquery-api.md#namespaces-and-path-validation) for prefixes.

#### Explore returned XML with hit xpath

Keep the product tree when you need several fields or want to inspect it later:

```python
with MLClient() as ml:
    cts = CtsService(
        ml.rest, namespaces={"p": "https://monasticus.com/mlclient/examples/products"}
    )
    hits = cts.search(
        expression="/p:catalog/p:product",
        query=cts.word_query("coffee"),
        pos=1,
    )
    for hit in hits:
        titles = hit.xpath(
            "p:title", p="https://monasticus.com/mlclient/examples/products"
        )
        prices = hit.xpath(
            "p:price", p="https://monasticus.com/mlclient/examples/products"
        )
        print(hit.content)  # The complete returned product is still available.
```

`hit.xpath()` mirrors `ElementTree.findall()`, with namespace prefixes passed as
keyword arguments. It makes no request and does not remove anything from
`hit.content`. It preserves the tree you retrieved, not parts excluded earlier
by `expression` or server-side `xpath`. JSON, text and binary hits do not support
this local XML operation.

`source_path` describes the returned node's location in the source document;
it is separate from both XPath operations. Partial results should not be written
back as whole documents.

### Get URIs from the URI lexicon

```python
with MLClient() as ml:
    cts = CtsService(ml.rest)
    uris = cts.uris(query=cts.collection_query("products"), pos=[1, 10])
    matching_uris = cts.uri_match("/products/*.json")
```

These methods always return a list of ordinary strings, or `[]` for no matches.
They require a URI lexicon in the database.

### Read indexed values with frequencies

Use a range index to retrieve distinct values and their frequencies:

```python
with MLClient() as ml:
    cts = CtsService(ml.rest)
    values = cts.values(
        cts.json_property_reference("category"),
        query=cts.collection_query("products"),
    )
    for hit in values:
        print(hit.value, hit.frequency)
```

This example requires a range index on the JSON property `category`.
`field_values("price")` similarly requires a range field index named `price`.
Missing indexes are reported as [`MarkLogicError`][mlclient.exceptions.MarkLogicError].

Individual lexicon results are [ValueHit][mlclient.models.ValueHit] objects:
`value` holds the parsed value, such as `str`, `Decimal` or `date`, and
`frequency` follows the lookup's item/fragment-frequency options. Aggregates
such as `estimate()` and `sum_aggregate()` return a list containing the parsed
aggregate value, without a hit wrapper. All result-producing CTS service methods
use this list contract, including `pos=1`. A JSON array remains one result
inside the outer list. Query/reference builders still return expressions.

This differs from `ml.eval.expression()`, which retains its empty/singleton/list
behavior when executing native builder expressions.

### Databases and async with CtsService

Search operations accept `database`, `txid` and `timeout` as keyword arguments.
For example, `cts.search(query=query, database="Documents", timeout=10)`.
Without `database`, the connected App Server's content database is used.

```python
from mlclient import AsyncMLClient
from mlclient.services import AsyncCtsService


async def find_products():
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        query = cts.collection_query("products")
        return await cts.search(query=query, pos=[1, 10])
```

Query builders are still synchronous; await only operations that execute.

For composing XQuery expressions, native argument conventions and results without
score/frequency wrappers, see the [XQuery API guide](../advanced/xquery-api.md).
