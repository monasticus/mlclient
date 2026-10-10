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
| A CTS query from the `cts` builder of `mlclient.xquery` | Serialized CTS JSON, `{"ctsquery": ...}` |
| A structured query from `mlclient.search.structured` | Serialized structured JSON, `{"query": ...}` |
| A string, such as `"coffee AND tea"` | Search API string query (`q`) |
| `None` (default) | No query; matches every document |

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

Both vocabularies compose with `&` (and), `|` (or) and `~` (not). Chained
operators build one flat query, so the following are equivalent:

```python
coffee_not_decaf = (
    cts.collection_query("products") & cts.word_query("coffee")
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

Operators combine queries of one vocabulary; mixing a CTS and a structured query
raises `TypeError`. The `repr` of a CTS query shows the arguments it was built
with, such as `WordQuery(text='coffee', weight=2)`.

The service serializes queries locally and sends them as JSON in the
`structuredQuery` parameter. A query argument that needs server evaluation, such
as a function call in a CTS value (including an `xs.*` cast of a literal),
raises `TypeError` before any request is made. Pass a ready-to-use Python literal
or evaluate the expression explicitly through `ml.eval` first.
See [which CTS queries serialize](queries.md#local-cts-serialization-and-limitations);
for elements in a namespace pass `fn.qname(uri, name)` rather than a prefixed name.
With inline options the service builds a
[combined query](https://docs.marklogic.com/REST/POST/v1/search) and uses POST;
without inline options it keeps the GET request. Serialization never requires eval.
For lexicon requests with inline options, the service carries CTS criteria in
the native `additional-query` option as serialized XML. On the tested versions,
MarkLogic otherwise ignores a combined query's `ctsquery` on `/values`. Existing
additional queries are retained and AND'd with the supplied criteria; `/search`
keeps native CTS JSON.

## Build query options

[SearchOptions][mlclient.search.options.SearchOptions] is a fluent builder.
It captures definition data and builds only the requested representation when
`to_json()`, `to_xml()` or `serialize()` is called. Passing it to a search service
serializes it when preparing the request. Building options alone creates neither
a JSON options document nor an XML tree. Mutable inputs are copied so later
changes do not affect existing definitions.

Use existing structured-query targets to identify indexes:

```python
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element, JsonProperty

price = Range(Element("price"), "xs:decimal")
options = (
    SearchOptions()
    .values("price", price)
    .range_constraint("price", price, options=["limit=10"])
    .sort(price, direction="descending")
    .control("return-metrics", True)
)

with MLClient() as ml:
    products = ml.search(options=options)
    documents = products.documents("coffee", pos=[1, 10])
    report = products.report("price GT 10")

# Use JsonProperty for a JSON property index, not Element.
json_price = Range(JsonProperty("price"), "xs:decimal")
```

Named constraints let string and constraint queries refer to a target by name:
`range_constraint` and `collection_constraint` (both calculate a facet unless
`facet=False`; the collection one takes an optional URI prefix),
`word_constraint` and `value_constraint` on an `Element` (optionally narrowed to
one of its attributes with `attribute=`), `JsonProperty` or `Field`, and
`container_constraint` on an `Element` or `JsonProperty`. A value constraint's
`node_type=` (`"number"`, `"boolean"`, `"null"`, default `"string"`) selects
which JSON values it matches:

```python
options = (
    SearchOptions()
    .word_constraint("title", Element("title"))
    .collection_constraint("type", prefix="products/")
)

with MLClient() as ml:
    uris = ml.search(options=options).uris("title:coffee type:beans")
```

Indexes must already exist in the target database; options do not create them.
`Range` also supports `Field`, `PathIndex` and an `Attribute` of an `Element`.
For URI or collection lexicons use `.values("uris", "uri")` or
`.values("collections", "collection")`; the database lexicon must be enabled.

The builder is mutable and chainable; serialization returns independent
representations, and two builders with the same definitions compare equal. To add an
option without a convenience method, use
`.add(native_json_members, *native_xml_children)`: every JSON definition needs
one search-namespace XML element of the same name, otherwise `ValueError` is
raised instead of silently dropping the option from one format. For JSON-only
service requests, `options={...}` also accepts native options members directly,
without the outer `{"options": ...}` wrapper.

## Find documents

`documents()` performs a multi-document read and returns
[Document][mlclient.models.Document] models in search result order: `XMLDocument`,
`JSONDocument`, `TextDocument` or `BinaryDocument`. MarkLogic sends only the
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
pass `pos` with them. Pass a range to read more, for example `pos=[1, 1000]`. `CtsService` differs here: without `pos` it returns every match. `category`
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
subset **before** `pos` selects a page; `limit=0` returns no values.

Tuples definitions raise `ValueError` in `values()`; use `tuples()` instead.

## Aggregate values

`aggregate(name, function, query=None, ...)` applies a built-in aggregate to a
values or tuples definition. It returns the parsed result, not a `ValueHit`:

```python
options = SearchOptions().values("price", Range(Element("price"), "xs:decimal"))

with MLClient() as ml:
    prices = ml.search(options=options)
    total_price = prices.aggregate("price", "sum")
    average_price = prices.aggregate("price", "avg")
    distinct_prices = prices.aggregate("price", "count")
```

`count` returns an integer, decimal sums and averages retain `Decimal`, and
statistical aggregates return floats. No result is `None` (for example, an
average with no matching values). Supported built-ins include min, max, median,
standard deviation, variance, correlation and covariance; binary statistics use
tuples.
Native-plugin aggregates remain available through `ml.rest.values`, including
`aggregate_path`; REST does not advertise a plugin result's type.

## Read co-occurrences

```python
options = SearchOptions().tuples(
    "price-day",
    Range(Element("price"), "xs:decimal"),
    Range(Element("day"), "xs:date"),
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
and the estimated total. These snippets are **not** whole `Document` objects;
use `documents()` to read actual content.

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

## Scope: databases, filters and options

Where a search runs and which options it uses is its
[SearchScope][mlclient.services.SearchScope]: `database`, `txid`, `collection`,
`directory`, `forest_name`, `options` and `timestamp`. Operations take only the
arguments of the operation itself, so the scope is set in one of two ways:

- **For a series of searches**, call the service: `ml.search(database="catalog",
  collection="products")` returns a new service bound to that scope. It sends no
  request and leaves `ml.search` unchanged; calling a scoped service narrows it
  further.
- **For one request**, pass `scope=SearchScope(...)` to an operation. It
  overrides only the fields it sets.

An omitted field is inherited; `None` clears an inherited value.

```python
from mlclient.services import SearchScope

with MLClient() as ml:
    catalog = ml.search(database="catalog", collection="products", options=options)
    coffee = catalog.documents("coffee", pos=[1, 20])
    archived = catalog.uris("coffee", scope=SearchScope(collection="archive"))
    everywhere = catalog.uris("coffee", scope=SearchScope(collection=None))

    with ml.transaction(database="catalog") as txn:
        pending = ml.search(**txn).uris("coffee")
```

`documents()` and `report()` also accept `transform` and `transform_params`: an
installed transform must preserve the native result contract of that operation.
Every operation accepts `timeout`. MarkLogic errors, such as an unknown values
name or a missing index, raise `MarkLogicError`.

For anything the service does not wrap, call the endpoints directly through
`ml.rest.search` (`get`, `post`, `delete`) and `ml.rest.values` (`get_list`,
`get`, `post`). `ml.rest.search.delete()` removes the documents of a collection or
directory; clearing a whole database requires `clear_database=True`. Those methods return raw `httpx.Response` objects and accept every
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

`CtsService` mirrors native `cts:` functions and runs them through `/v1/eval`.
It is more flexible than `ml.search` - every search, lexicon and aggregate
function, scored `SearchHit` results, subtree search and composition with other
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

A selected position returns a one-item list; a missing position returns `[]`.
A two-item list or tuple selects an inclusive range.
Use an explicit ordering option when your application needs stable page ordering;
see [XQuery API: selection and ordering](xquery-api.md#selection-and-ordering).

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
`MarkLogicError` with code `MLCLIENT-INVALID-PATH`; empty paths are rejected
locally. For example, `/fn:string()` is not an extraction path. Native search
can nevertheless return text and JSON scalar nodes as well as XML/JSON trees.
See [namespace bindings](xquery-api.md#namespaces-and-path-validation) for prefixes.

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
Missing indexes are reported as `MarkLogicError`.

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
score/frequency wrappers, see the [XQuery API guide](xquery-api.md).
