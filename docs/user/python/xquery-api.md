# XQuery API

The singletons in `mlclient.functions.xqy` mirror native XQuery functions.
They build composable expressions without making requests. Pass a complete
expression to `ml.eval.expression()` to execute it in one request.

!!! note "Experimental API"
    The expression builders and CTS service are experimental.

## CTS: search, lexicons and queries

Start with the [search guide](search.md) when you want `SearchHit` objects with
scores or `ValueHit` objects with frequencies. Use the `cts` **singleton** from
`mlclient.functions.xqy` when you want native results or need to compose CTS
under another XQuery function. It is not a `CtsService` instance.

### Native results without scores or frequencies

```python
from mlclient import MLClient
from mlclient.functions.xqy import cts

with MLClient() as ml:
    documents = ml.eval.expression(
        cts.search(query=cts.collection_query("products")).pos([1, 10]),
    )
    categories = ml.eval.expression(
        cts.values(cts.json_property_reference("category")),
    )
```

The first call returns parsed nodes directly, not `SearchHit` objects. The
second returns indexed values directly, not `ValueHit` objects; it requires a
range index on `category`. Neither expression adds `cts:score` or `cts:frequency`
to the query. There are no alternating content/measure parts to decode yourself.
The CTS service adds those calls and pairs their results internally, in the
same request, when you want the additional information.

The evaluator returns `[]` for an empty sequence, the item for a singleton, and
a list for multiple items. A single JSON array is returned directly, without
an extra outer list. “Native” here means the function's own results, still parsed
into Python types. For original response-part payloads, pass `output_type=bytes`.
That option does not turn service hits into raw hits.

Unlike the evaluator, all result-producing CTS service methods always return a
list, even for a single result or aggregate. Query builders do not execute and
return expressions instead.

### Compose CTS under another function

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

Each evaluation composes everything on the server. `count` is an integer and
the existence results are booleans. This example requires an element range index
on `price`. Python scalar values are bound as typed external variables, not
inserted into the source: user-provided text is safe in `cts.word_query(text)`.

### Native argument conventions

Required native arguments keep their relative order and may be positional.
Optional arguments are keyword-only, in their native order. For example:

```python
query = cts.collection_query("products")
cts.uris(query=query)
cts.values(cts.element_reference("price"), start=10, query=query)
```

Use `query=` consistently. `uris` has only optional native arguments; `values`
requires its range-index argument first. This is not a query-first convention.
For native signatures that interleave required and optional arguments, Python
groups required arguments first. For example, `geospatial_co_occurrences`
requires both lexicon names before the optional child names. Compilation restores
the native argument slots, including empty placeholders.

`search(expression=None, query=None, ...)` permits omitting the native required
slots: the expression defaults to `/` and the query to the empty sequence.
`estimate` also permits omitting its query. Services keep these builder contracts
and add execution options such as database, timeout and `pos`.

### Selection and ordering

Builders support `.pos(position)` and `.pos([start, end])`. Positions are
one-based and range endpoints are inclusive. Bounds accept positive integers
or `fn.last()`:

```python
from mlclient import MLClient
from mlclient.functions.xqy import cts, fn

with MLClient() as ml:
    remaining = ml.eval.expression(
        cts.uris(query=cts.collection_query("products")).pos([2, fn.last()]),
    )
```

`fn.last()` uses the size of the selected sequence and may require counting all
results. For value-ordered pages, configure a range index and specify ordering:

```python
from mlclient import MLClient
from mlclient.functions.xqy import cts

with MLClient() as ml:
    page = ml.eval.expression(
        cts.search(
            query=cts.collection_query("products"),
            options=cts.index_order(
                cts.json_property_reference("price"),
                options="ascending",
            ),
        ).pos([11, 20]),
    )
```

The service offers the equivalent `pos=[11, 20]` and `pos=1` forms.
For XML selection, see the three levels in [Work with XML](search.md#work-with-xml).
The expression-builder equivalent of server-side `xpath` is `.xpath(path)`;
apply it **after** `.pos()` to select hits before extracting nodes.

Applying `.xpath()` preserves search order. In native XQuery, use
`cts:search(...)[1 to 10] ! p:product/p:title`, not
`cts:search(...)[1 to 10]/p:product/p:title`: the latter imposes document order,
which can undo relevance or index ordering. See MarkLogic's explanation of
[relevance order versus XPath document order](https://docs.marklogic.com/9.0/guide/search-dev/relevance#id_23654).

### Namespaces and path validation

Pass prefixes once for the complete expression, including nested calls:

```python
from mlclient import MLClient
from mlclient.functions.xqy import cts, fn

with MLClient() as ml:
    count = ml.eval.expression(
        fn.count(
            [
                cts.search(expression="/p:product"),
                cts.search(expression="/p:accessory"),
            ]
        ),
        namespaces={"p": "https://monasticus.com/mlclient/examples/products"},
    )
```

Bindings become XQuery namespace declarations. An empty prefix sets the default
element namespace: `namespaces={"": "https://monasticus.com/mlclient/examples/products"}` allows `/product`.
For QNames, use `xs.qname("p:item")` with a declared prefix, or
`fn.qname("https://monasticus.com/mlclient/examples/products", "p:item")` to supply the URI explicitly.

A service can hold default bindings; per-call bindings override matching prefixes
without changing those defaults:

```python
from mlclient import MLClient
from mlclient.services import CtsService

with MLClient() as ml:
    cts = CtsService(
        ml.rest, namespaces={"p": "https://monasticus.com/mlclient/examples/products"}
    )
    seasonal = cts.search(
        expression="/p:product",
        namespaces={"p": "https://monasticus.com/mlclient/examples/seasonal-products"},
    )
```

The same `namespaces` keyword is accepted by search, lexicon and estimate calls,
including their async counterparts. Path references also accept a local map:
`cts.path_reference("/p:product/p:price", namespaces={"p": "https://monasticus.com/mlclient/examples/products"})`.
That map takes precedence for the reference, not for the rest of the expression.

Paths inserted as code (search expressions, `.xpath()` and `xpath()` expressions)
are validated together before executing the composed expression, regardless of
nesting. `MLCLIENT-INVALID-PATH` identifies each rejected path's role and variable
binding. Only after validation does `xdmp:value` compile and execute the generated
body. Variables inside these paths are not accepted; use query builders for
dynamic values. Valid paths must still meet the native function's requirements.

String arguments such as `cts.path_range_query("/p:product/p:price", "=", 10)`
and `cts.path_reference(...)` remain externally bound data. They do not need
this code-insertion guard; the receiving MarkLogic function checks their path
syntax, namespaces and index requirements and reports native errors.

### Result types

Both native eval and the service parse content eagerly, including mixed results.
The service holds search content in `SearchHit.content` and lexicon values in
`ValueHit.value`; it does not provide lazy or raw-content aliases.

| Returned value | Parsed Python representation |
| --- | --- |
| XML document / element | `ElementTree` / `Element` |
| JSON object / array | `dict` / `list` |
| JSON number, boolean or null | Number, `bool` or `None` |
| Text, JSON string property or XML attribute | `str` |
| XML comment or processing instruction | Serialized text as `str` |
| Binary | Unchanged `bytes` |
| Atomic lexicon value | Native-type conversion, e.g. `int`, `Decimal`, `date` |
| Unrecognized primitive | Unchanged `bytes` |

The returned node determines the type, not its source URI. `xs:decimal` is
preserved as Python `Decimal`; `xs:float` and `xs:double` become Python `float`.
Malformed XML/JSON fails during the call, not when accessing the result.

Service frequencies follow native item/fragment-frequency options, not an assumed
document count; see [cts:frequency](https://docs.marklogic.com/cts:frequency).
Lexicon `map` output is not a value sequence: evaluate
`cts.values(reference, options="map")` through `ml.eval.expression` for that
native shape. Frequency-bearing service methods reject literal `"map"` options
with `ValueError` before making a request. When options are computed by an XQuery
expression, map output is rejected on the server with `MLCLIENT-LEXICON-MAP`.

### MarkLogic versions

Builders expose the same functions regardless of the connected server. Native
version restrictions still apply; unavailable functions raise `MarkLogicError`.

| Function | Requires |
| --- | --- |
| `cts.document_root_query` | MarkLogic 11+ |
| `cts.document_format_query` | MarkLogic 11+ |
| `cts.document_permission_query` | MarkLogic 11+ |
| `cts.iri_reference` | MarkLogic 11+ |

Consult the [`cts` reference][mlclient.functions.xqy.cts] and the
[native reference](https://docs.marklogic.com/cts) for individual requirements.

## FN: compose standard functions

`fn` mirrors all 148 functions in the MarkLogic function reference, including
functions restricted to XSLT or legacy `0.9-ml`. Expressions compile as `1.0-ml`;
a builder does not remove native restrictions. For example, `fn.last()` belongs
inside a predicate and XSLT grouping functions need an XSLT context.

Names use snake case (`fn.function_lookup`, `fn.date_time`, `fn.qname`). Python
keywords have a trailing underscore, as in `fn.not_`. Omitting an optional
argument differs from passing `None`: `fn.collection()` uses the default
collection, while `fn.collection(None)` passes the empty sequence.

### Strings versus XPath expressions

An ordinary string is a value, not executable code. Use `xpath()` explicitly
when a general-purpose function should operate on nodes selected by a path:

```python
from mlclient import MLClient
from mlclient.functions.xqy import fn, xpath

with MLClient() as ml:
    one = ml.eval.expression(fn.count("/product"))  # 1: one string value
    products = ml.eval.expression(fn.count(xpath("/product")))  # Matching nodes
```

`xpath()` always registers validation, whether evaluated directly or nested
inside another expression. It accepts MarkLogic extraction paths, not arbitrary
XQuery, XML constructors or inline functions. Functions with an explicit path
parameter, such as `cts.search(expression="/product")`, do not need the wrapper.

### Higher-order functions

Higher-order functions take XQuery function expressions, not Python callables:

```python
from mlclient import MLClient
from mlclient.functions.xqy import fn

with MLClient() as ml:
    upper = fn.function_lookup(
        fn.qname("http://www.w3.org/2005/xpath-functions", "upper-case"),
        1,
    )
    result = ml.eval.expression(fn.map(upper, ["red", "blue"]))
```

Other available namespaces include `xs` for typed values and `xdmp` for the
supported MarkLogic-specific builders. See the
[XQuery API reference](../../reference/mlclient/functions/xqy/index.md) for the actual
exported surface; availability of a namespace does not imply every native
function has a builder.

## Custom XQuery expressions

For a deployed library module, define a namespace family such as `Label` with
static methods returning public
[ModuleFunctionCall][mlclient.functions.xqy.ModuleFunctionCall] expressions.
Each method provides the function's local name, arguments, namespace URI and
module path. No XQuery rendering or shared import registry is required.

The [custom module recipe](../../recipes.md#call-a-custom-xquery-module) shows
the XQuery library, the `Label` family and `label` singleton, and composition with
`ml.eval.expression(fn.string_length(label.normalize(...)))`. Module loading is
handled internally; independent libraries do not compete for prolog prefixes.

For expressions beyond module function calls, subclass the public
[XqyExpression][mlclient.functions.xqy.XqyExpression] and
implement `render(ctx: XqyCompilationContext) -> str`. Bind runtime values with
`ctx.bind(value, atomic_type)`; `compile()` returns XQuery source and bindings.
Custom expressions compose with the same builders and evaluator as built-in ones.

For complete XQuery programs use `ml.eval.xquery(code, variables=...)`.
Keep custom rendering developer-controlled and bind runtime data; `xpath()` is
only for validated paths, not an escape hatch for arbitrary source.
