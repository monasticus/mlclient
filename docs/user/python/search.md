# Search

!!! warning "Experimental API"
    The builders and namespace services are experimental. This revision changes
    some POC signatures and result shapes; see the migration notes below.

The API mirrors MarkLogic's `cts:` functions: familiar names and arguments cover
both simple searches and nested queries without introducing a second query
language. Python methods use underscores where XQuery uses hyphens.

Every builder returns an immutable [Expr][mlclient.functions.Expr]. Expressions
can be arguments to other expressions **or the root of an evaluation**. The
`fn`, `xdmp` and `xs` namespaces demonstrate this composition; they do not use
separate compilers or execution paths. Builders perform no I/O.

The `cts` namespace exposes 191 non-deprecated MarkLogic 12 functions. This
includes query constructors, references, orders, geospatial and temporal value
constructors, search and estimate, lexicon operations, aggregates, text
processing, query registration, classification and triples. Accessors that only
decompose an existing query or opaque CTS value are intentionally omitted. For
example, use `cts.element_range_query(...)`, but retain its inputs in your
application instead of calling `cts:element-range-query-value` through this API.

## Build, compose and execute

```python
from decimal import Decimal

from mlclient import MLClient
from mlclient.functions import cts, fn, xpath, xs

query = cts.and_query([
    cts.collection_query("products"),
    cts.element_range_query("price", ">=", Decimal("19.95")),
])
hits = cts.search(xpath("/product"), query)

with MLClient() as ml:
    page = ml.eval.expression(hits.window(1, 10))  # always a list
    count = ml.eval.expression(fn.count(hits))   # [number_of_hits]
    text = ml.eval.expression(xs.string(fn.count(hits)))  # ["..."]
```

The example requires an element range index for decimal `price`. MarkLogic
validates index availability, argument types and searchable paths. For example,
`cts.search` requires a fully searchable node expression; `xdmp.exists` accepts
partially searchable expressions. Use `fn.exists` for arbitrary sequences.
[Search reference](https://docs.marklogic.com/cts:search),
[existence reference](https://docs.marklogic.com/xdmp:exists).

`window(lo, hi)` selects inclusive, one-based positions. Both bounds must be
integers (not booleans), with `1 <= lo <= hi`. The positional predicate executes
on the server and can benefit from MarkLogic's lazy search evaluation. It does
not change filtered search into unfiltered search or guarantee a particular
query plan.

## Values, sequences and source

| Python input | XQuery representation |
| --- | --- |
| `Expr` | Nested expression |
| `None`, `[]`, `()` in a value position | Empty sequence |
| List or tuple | Sequence; nested sequences flatten on the server |
| String | One bound `xs:untypedAtomic` value, never characters or source |
| `bool`, `int`, `float` | `xs:boolean`, `xs:integer`, `xs:double` |
| `Decimal` | Exact `xs:decimal`; nonfinite decimals are rejected |
| `date`, `datetime` | ISO value cast to `xs:date` or `xs:dateTime` |

MarkLogic still enforces its native numeric ranges (for example, an integer
outside its supported range raises a server cast error). Numeric and temporal
values use JSON-safe bindings; large integers and decimals
are sent as lexical strings to avoid JSON numeric precision loss. Floating-point
NaN and infinities use XML Schema lexical forms. Lists are copied into immutable
expression children, so changing an input list later cannot change a query.
Dictionaries, generators, sets and arbitrary Python objects are rejected.
A Python list means an XQuery sequence, **not** a JSON array node.

`xs` constructors also accept expressions: `xs.double(fn.count(hits))` casts the
result on the server. QName arguments accept `xs.qname("price", "urn:products")`;
sequence-valued element-query arguments also accept lists of names.

For optional arguments, `None` means omission; `[]` or `()` explicitly passes an
empty sequence. Omitted trailing arguments are removed. An omitted slot before
a supplied later argument becomes `()`, preserving the native argument order.
Options accept a single string, a list/tuple, or an expression. Search options
may also contain expressions producing native `cts:order` values.

### Trusted XPath

`cts.search()` searches the root expression `/` by default. A custom path must
be an expression, such as `xpath("/Q{urn:products}product")`.

[xpath][mlclient.functions.xpath] embeds **trusted developer-controlled source**.
It does not parse or sanitize XQuery and is not a sandbox. Never wrap user input
in it. Dynamic text, URIs and comparison values belong in builder arguments,
where they are external variables and cannot become executable source.

Use EQNames (`Q{namespace-uri}local-name`) for namespaced paths. For
`cts.path_reference`, `namespaces` accepts an expression returning a native
`map:map`; it does not accept a Python dictionary. This keeps native objects
composable without inventing a second object serialization scheme.

Compilation uses `xquery version "1.0-ml";`. Source, including whitespace inside
literals and comments, is preserved by the eval transport.

## Results and execution options

[EvalService.expression][mlclient.services.EvalService.expression] and its async
counterpart compile once and send one `/v1/eval` request. They return one Python
list entry per server result item:

| Server sequence | Python result |
| --- | --- |
| Empty | `[]` |
| One integer | `[42]` |
| Two strings | `["a", "b"]` |
| One JSON array node | `[[1, 2]]` |

Integers become `int`, decimals become `Decimal`, floating-point values become
`float`, and dates/timestamps become `date`/`datetime`. XML documents become
`ElementTree`, XML elements become `Element`, and JSON nodes are decoded as
JSON. Unsupported primitives, including QName and serialized query/reference
objects, remain bytes. Use `output_type=str` or `output_type=bytes` for raw
per-item output.

Python temporal limits apply: dates discard an XQuery timezone, datetimes retain
it, fractional seconds have microsecond precision, and years must fit Python's
supported range. Parsing errors are propagated instead of silently returning a
value of an unrelated type.

Allowed execution keywords are `database`, `txid`, `output_type` and `timeout`.
Unknown keywords, including `variables` and names such as `v0`, are rejected;
they cannot override compiler bindings. The HTTP timeout inherits the client's
setting when omitted and does not impose a server query time limit.

Raw `ml.eval.xquery(...)` and `javascript(...)` keep their existing result
contract (singleton collapsing and decimal-to-float conversion). Use
`expression(...)` for the stable outer sequence and precise decimal conversion.
Raw eval source is now sent verbatim rather than having newlines removed.

## Convenience services

```python
from mlclient import MLClient
from mlclient.functions import cts, xpath
from mlclient.services import CtsService, FnService, XdmpService

with MLClient() as ml:
    query = cts.collection_query("products")
    search = CtsService(ml.rest)
    page = search.search(xpath("/product"), query, range=(11, 20))
    uris = search.uris(query)  # requires the URI lexicon
    count = FnService(ml.rest).count(cts.search(query=query))  # int
    present = XdmpService(ml.rest).exists(cts.search(query=query))  # bool
```

Services delegate to the common expression evaluator; they do not inherit the
builder namespaces. `search`, `uris` and `values` always return lists.
`estimate` and `count` return one integer; `exists` and `empty` return one boolean.
An unexpected aggregate cardinality raises an error. The list operations accept
`range=N` (positions 1 through N) or `range=(lo, hi)`.

`AsyncCtsService`, `AsyncFnService`, `AsyncXdmpService` and
`AsyncEvalService.expression` have the same contracts, with calls awaited:

```python
from mlclient import AsyncMLClient
from mlclient.functions import fn

async def count_items():
    async with AsyncMLClient() as ml:
        return await ml.eval.expression(fn.count([1, 2]))  # [2]
```

## Server versions

Builders do not guess the server version or maintain a runtime feature registry.
The catalog follows the MarkLogic 12 function reference. The server reports a
function unavailable in an older release through `MarkLogicError`; particular
options and index configurations can also have version requirements. For
example, `cts.document_root_query` requires MarkLogic 11 or later. Consult the
[native CTS reference](https://docs.marklogic.com/cts) for the function you use.

| Builder | MarkLogic 10 | MarkLogic 11 | MarkLogic 12 |
| --- | --- | --- | --- |
| `document_root_query` | Unavailable | Available | Available |
| `document_format_query` | Unavailable | Available | Available |
| `document_permission_query` | Unavailable | Available | Available |
| `iri_reference` | Unavailable | Available | Available |

These are the four supported names added between the versioned CTS references
for [10](https://docs.marklogic.com/10.0/cts) and
[11](https://docs.marklogic.com/11.0/cts); the 12 reference adds no further names
in this catalog. Availability of a name does not guarantee every option on
every minor release, or the presence of required indexes and permissions.

One `Cts` namespace serves all versions. Building an expression has no target
server, so it emits no version warning and does not hide methods. The same
expression can be reused with different clients. Execution propagates the
server's error (for example `XDMP-UNDFUN` on ML10), including when an unavailable
function is nested. Applications supporting multiple releases should choose
queries from their deployment requirements; the library does not silently
rewrite queries to approximate older-server behavior.

## Native objects and callback expressions

Use an `Expr` returning XML or a native map for parameters such as
`cts.parse(..., bindings=xpath("map:map()"))`. A Python dictionary is not a
MarkLogic map. `highlight` and `walk` accept trusted expressions referencing
MarkLogic's callback variables, for example
`cts.highlight(xpath("<p>alpha</p>"), cts.word_query("alpha"),
xpath("<b>{$cts:text}</b>"))`. The callback runs on MarkLogic, not in Python;
the same trusted-source rules apply as for any `xpath(...)` input.

`triple_range_query` accepts a single operator (including `"sameTerm"`) or three
operators for subject, predicate and object. An empty sequence uses the native
default. Unlike scalar range comparisons, these arguments are validated by
MarkLogic. `geospatial_co_occurrences(first, second, ...)` takes both required
lexicon names first in Python and places the optional child names in their
native XQuery positions when compiling.

## Migrating from the POC

- Replace path strings with explicit `xpath(...)` in `search` and `xdmp.exists`.
- Replace `cts.document_root(...)` with `cts.document_root_query(...)`.
- Replace `and_query(..., ordered=True)` with `options="ordered"` (or
  `"unordered"` for false). `or_query` also accepts native options.
- Replace `near_query(..., weight=...)` with `distance_weight=...`.
- `json_property_value_query` calls its second argument `value`, including when
  passing a keyword; it accepts booleans and numbers as well as strings.
- Create queries through `cts`, `fn`, `xdmp`, `xs`; service instances execute
  their documented conveniences and no longer expose inherited builders.
- Remove service `version=...` arguments. Account for lists from sequence
  operations and exact `Decimal` results from expression execution.

## Extending the catalog

For another native function, verify its XQuery signature for supported servers,
then add one pure builder returning the existing function-call expression.
Keep native parameter order, cardinality and omitted optional slots. Reuse the
shared value conversion; do not add another compiler, eval call or version gate.
Use native names converted to Python underscores and document version limits.

Test the actual request bindings and a nested/root evaluation on MarkLogic.
Only add a service convenience when it adds a useful result contract; any new
builder already executes through `ml.eval.expression`. Accessors and deprecated
functions remain outside the catalog unless a concrete use case justifies them.
