# Search

MLClient provides a Python API that mirrors MarkLogic's XQuery functions.
It is designed to grow beyond search while keeping familiar function names,
arguments and composition. Python uses underscores where XQuery uses hyphens.

Search is central to working with MarkLogic, so
[CtsService][mlclient.services.CtsService] adds a convenient way to build queries
and execute searches through one `cts` object.

!!! note "Experimental API"
    This API is experimental while its design is validated in real applications.

The public expression type is
`from mlclient.functions.xqy import Expression`. It belongs to XQuery, not the
language-neutral `mlclient.functions`: it compiles XQuery source and bindings,
with XQuery namespaces, paths and positional semantics. A future SJS expression
type need not share that implementation or inheritance hierarchy.

`Cts`, `Fn`, `Xs` and `Xdmp` are public namespace-builder classes; their lowercase
instances are the usual entry points. Custom expressions can subclass
`Expression` and implement `render(ctx: CompilationContext) -> str`, importing
both types from `mlclient.functions.xqy`. Use `ctx.bind(value, atomic_type)`
for runtime data and `compile()` to obtain source plus bindings. Internal tree
nodes are implementation details, not required imports. For validated
projection compose `.project("p:title")` after `.index(...)` or `.range(...)`.

## Search with CtsService

```python
from mlclient import MLClient
from mlclient.services import CtsService

with MLClient() as ml:
    cts = CtsService(ml.rest)
    products = cts.search(
        query=cts.and_query([
            cts.collection_query("products"),
            cts.word_query("coffee"),
        ]),
    )
```

Use `CtsService` when CTS search is the operation you want to execute. Its query
builders mirror their XQuery counterparts: if you already use MarkLogic, you
can combine familiar collection, word, element, property and range queries.

The `search`, `uris`, `values` and `estimate` methods execute their expressions.
Other inherited methods build queries or expressions without sending requests.

### Python argument conventions

Native required arguments keep their order and may be positional. Native
optional arguments are keyword-only, in their native order: for example,
`uris(*, start=None, options=None, query=None, ...)` and
`values(range_indexes, *, start=None, options=None, query=None, ...)`.
This avoids ambiguous positional placeholders; generated XQuery still uses
the exact native argument slots. Use `query=` consistently in search examples.

When required and optional arguments are interleaved natively, Python groups
required arguments first. The catalog's example is
`geospatial_co_occurrences(geo_element_name_1, geo_element_name_2, *,
child_1_name_1=None, ...)`: native child slots precede the second lexicon name.
The builder restores those slots when compiling, including empty placeholders.
This is a required/optional grouping rule, not a query-first convention.

`search(expression=None, query=None, ...)` additionally allows omitting the
native required slots: `expression=None` selects `/`, and `query=None` passes
the empty sequence. `estimate` likewise permits omitting its query. These are
explicit convenience defaults, not reordered arguments. Services keep the
builder contracts and add keyword-only execution options and range/index.

## Select a range of URIs

```python
from mlclient import MLClient
from mlclient.services import CtsService

with MLClient() as ml:
    cts = CtsService(ml.rest)
    uris = cts.uris(
        query=cts.and_query([
            cts.collection_query("products"),
            cts.json_property_value_query("active", True),
        ]),
        range=[1, 10],
    )
```

Positions are one-based and inclusive: `[1, 10]` selects the first ten results
on the server. Empty results return `[]`, a single result returns the item,
and multiple results return a list. `estimate` returns one integer. The methods also accept evaluation options such as `database`
and `timeout`.

## Select one result

```python
from mlclient import MLClient
from mlclient.functions.xqy import fn
from mlclient.services import CtsService

with MLClient() as ml:
    cts = CtsService(ml.rest)
    first = cts.search(query=cts.collection_query("products"), index=1)
    last_uri = cts.uris(query=cts.collection_query("products"), index=fn.last())
    remaining = cts.uris(
        query=cts.collection_query("products"), range=[2, fn.last()],
    )
```

`index` and range bounds accept positive integers or `fn.last()`. Using both
`index` and `range` raises `ValueError`. A missing position returns `[]`.
`fn.last()` uses the size of the sequence being selected and may require counting
all results. Builders also support `.index(...)` and `.range(start, end)`.

Python scalar values are bound as typed external variables. For QNames, use
`xs.qname("p:item")` with a declared prefix, or `fn.qname("urn:products", "p:item")`
to supply the namespace URI explicitly.

Both `ml.eval.expression` and `ml.eval.xquery` preserve `xs:decimal` values as
Python `Decimal`. `xs:float` and `xs:double` return Python `float`.

## Compose CTS under another function

When CTS is part of a larger expression, use the XQuery namespace singletons
and execute the complete expression with `ml.eval.expression`:

```python
from mlclient import MLClient
from mlclient.functions.xqy import cts, fn, xdmp

with MLClient() as ml:
    values = cts.values(cts.element_reference("price"))
    count = ml.eval.expression(fn.count(values))
    present = ml.eval.expression(fn.exists(values))
    matching_documents = ml.eval.expression(
        xdmp.exists(cts.search(query=cts.collection_query("products"))),
    )
```

Each evaluation sends the complete expression in one request. Namespace
singletons build expressions; they do not execute them. The generic evaluator
returns `[]` for an empty sequence, the item for a singleton, and a list for
multiple items. Here, `count` is an integer and the existence results are booleans.
A single JSON array is returned directly, without an extra outer list.

Strings used as query values are bound as data rather than inserted into XQuery
source. For example, user-provided search text can be passed directly to
`cts.word_query(text)`.

## Paths and namespaces

### Extract part of each search hit

`search(..., xpath="p:product/p:title", range=[1, 10])` first searches, then
selects the first ten hits, then extracts titles from each selected hit.
It executes the equivalent of `(cts:search(...)[...]) ! (p:product/p:title)`:
the simple-map operator preserves hit order rather than sorting all extracted
nodes into document order. A hit may produce zero or many results, so the final
result count need not equal the range size. The usual empty/singleton/list
return convention applies to the extracted sequence.

The path uses the same namespace declarations and native restricted-XPath
validation as `expression`. A relative path starts at each hit; a leading `/`
starts at that hit's document root. For `expression="/p:product"`, use
`xpath="p:title"`; for the default document-node expression, use
`xpath="p:product/p:title"`. Empty strings are rejected. This is not arbitrary
XQuery: constructs such as `.` or `./title` are not accepted by the native
extraction-path validator. `xpath=None` leaves search hits unchanged.

### Select the searchable expression

Pass a searchable XPath directly as a string. The library validates paths with
MarkLogic's native validators before executing the composed expression.

```python
from mlclient import MLClient
from mlclient.services import CtsService

with MLClient() as ml:
    cts = CtsService(ml.rest, namespaces={"p": "urn:products"})
    products = cts.search(
        "/p:product",
        query=cts.path_range_query("/p:product/p:price", ">=", 10),
    )
    seasonal = cts.search(
        "/p:product",
        namespaces={"p": "urn:seasonal-products"},
    )
```

Namespaces become XQuery declarations. An empty prefix selects the default
element namespace: `namespaces={"": "urn:products"}` allows `/product`.
Per-call bindings override matching service defaults without changing them.
The same `namespaces` keyword is accepted by `search`, `uris`, `values`,
`estimate`, their async counterparts, and `ml.eval.expression`.

For generic composition, namespaces apply to the complete expression:

```python
from mlclient import MLClient
from mlclient.functions.xqy import cts, fn

with MLClient() as ml:
    count = ml.eval.expression(
        fn.count([
            cts.search("/p:product"),
            cts.search("/p:accessory"),
        ]),
        namespaces={"p": "urn:products"},
    )
```

Literal searchable paths and index paths, including lists of paths and paths
inside nested calls, are checked together. `MarkLogicError` with code
`MLCLIENT-INVALID-PATH` identifies each rejected path before the main expression
runs. Valid paths must also meet the native function's requirements, such as
being searchable or having a corresponding index.

Validation uses MarkLogic's restricted XPath syntax, including supported
functions in predicates. Variables inside these path strings are not accepted;
pass dynamic search values through query builders. Explicit `xpath(...)` used
for arbitrary expressions is trusted XQuery code, not a sandbox. When used as
the searchable path argument, its source is validated too. Computed `Expression`
arguments to native string-path parameters remain expressions and are checked
by the receiving native function when evaluated; they are not included in the
literal-path preflight.

Path references can also receive a local namespace map, for example
`cts.path_reference("/p:product/p:price", namespaces={"p": "urn:products"})`.
This map takes precedence for that reference; it does not change the namespace
declarations for the rest of the expression.

## Async searches

```python
from mlclient import AsyncMLClient
from mlclient.services import AsyncCtsService

async def find_products():
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        return await cts.search(query=cts.collection_query("products"))
```

Query construction is synchronous; execution is awaited. Generic expressions
use `await ml.eval.expression(...)` in the same way.

## MarkLogic versions

The Python API is version-agnostic: it exposes the same functions regardless
of the connected server. You are responsible for using functions supported by
your MarkLogic version. Requirements are documented with the corresponding
function. The server reports an unavailable function through `MarkLogicError`.

| Function | Requires |
| --- | --- |
| `cts.document_root_query` | MarkLogic 11+ |
| `cts.document_format_query` | MarkLogic 11+ |
| `cts.document_permission_query` | MarkLogic 11+ |
| `cts.iri_reference` | MarkLogic 11+ |

Consult the [Cts reference][mlclient.functions.xqy.Cts] for supported functions
and the [native MarkLogic reference](https://docs.marklogic.com/cts) for
version-specific options.

## FN composition

The `fn` namespace mirrors all 148 functions in the MarkLogic function reference,
including functions restricted to XSLT or the legacy `0.9-ml` dialect. Each method
retains the native restrictions in its documentation. Expressions compile as
`1.0-ml`; a legacy-only function does not become available in that dialect simply
because it has a Python builder. Context functions such as `fn.last()` belong
inside a predicate; XSLT grouping functions require the corresponding XSLT context.

Python names use snake case: `fn.function_lookup`, `fn.date_time`, and `fn.qname`.
Python keywords have a trailing underscore, for example `fn.not_` and the `in_`
argument to `fn.analyze_string`. Optional arguments can be omitted; explicit
`None` means an empty XQuery sequence. For example, `fn.collection()` uses the
native default collection, while `fn.collection(None)` passes `()`.

Higher-order functions such as `fn.map` and `fn.filter` accept XQuery function
expressions, not Python callables:

```python
from mlclient import MLClient
from mlclient.functions.xqy import fn

with MLClient() as ml:
    upper = fn.function_lookup(
        fn.qname("http://www.w3.org/2005/xpath-functions", "upper-case"), 1,
    )
    result = ml.eval.expression(fn.map(upper, ["red", "blue"]))
```
