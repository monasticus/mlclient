# Search

Use `CtsService` to find documents, retrieve their URIs or read indexed values.
Build a query, pass it to a search operation, and work with parsed Python results.

## Find documents

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

## Select results

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

## Work with XML

There are three places to select XML nodes. The first two run in MarkLogic;
the third runs locally in Python:

| Selection | Where | What it changes |
| --- | --- | --- |
| `search(expression=...)` | XQuery, inside `cts:search` | Which candidate nodes are searched and filtered against `query` |
| `search(xpath=...)` | XQuery, after search and `pos` | Which parts of each matching node are sent back |
| `hit.xpath(...)` | Python, after retrieval | Which elements you access in the already returned XML tree |

### Choose what to search with expression

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

### Return less XML with search xpath

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

### Explore returned XML with hit xpath

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

## Get document URIs

```python
with MLClient() as ml:
    cts = CtsService(ml.rest)
    uris = cts.uris(query=cts.collection_query("products"), pos=[1, 10])
    matching_uris = cts.uri_match("/products/*.json")
```

These methods always return a list of ordinary strings, or `[]` for no matches.
They require a URI lexicon in the database.

## Read indexed values

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

## Choose a database or use async

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
