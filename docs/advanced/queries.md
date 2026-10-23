# Structured and CTS queries

Choose a query vocabulary, then use the same API to serialize and search:

| | Structured queries | CTS queries |
| --- | --- | --- |
| Builder | [`sq`][mlclient.search.sq] from [`mlclient.search`][mlclient.search] | [`cts`][mlclient.xquery.Cts] from [`mlclient.xquery`][mlclient.xquery] |
| Native format | Search API structured JSON/XML | CTS JSON/XML |
| Local serialization | `serialize()`, `to_json()`, `to_xml()` | `serialize()`, `to_json()`, `to_xml()` |
| Combined query | `to_combined_query()` under `query` | `to_combined_query()` under `ctsquery` |
| REST execution | `ml.search` | `ml.search` |
| XQuery compilation and execution | Not supported | `compile()`, `ml.eval.expression()`, [`CtsService`][mlclient.services.CtsService] |

## Shared serialization API

Both families implement [`QueryComponent`][mlclient.search.QueryComponent] and
[`SearchQuery`][mlclient.search.SearchQuery]. The API is shared; their native wire formats
remain distinct. Build equivalent queries with either vocabulary:

```python
from xml.etree.ElementTree import tostring

from mlclient.search import sq
from mlclient.xquery import cts

structured = sq.query(sq.and_(sq.collection("reports"), sq.term("blue")))
cts_query = cts.and_query(
    [
        cts.collection_query("reports"),
        cts.word_query("blue"),
    ]
)

for query in (structured, cts_query):
    json_query = query.serialize()  # Same as serialize("json") or to_json().
    xml_query = query.serialize("xml")  # Same as to_xml(); an ElementTree element.
    xml_text = tostring(xml_query, encoding="unicode")
    combined = query.to_combined_query()
```

Use `to_json()` when you need a Python dictionary, or `to_xml()` when you need
an ElementTree element. MLClient builds either representation locally from the
query object, without making a server request. Each call returns a new result,
so you can modify it without changing the query.

## Execute over REST

[`ml.search`](../guides/search.md) accepts both query families and serializes them locally:

```python
from mlclient import MLClient

with MLClient() as ml:
    structured_documents = ml.search.documents(structured)
    cts_documents = ml.search.documents(cts_query)
```

### Native JSON or Python query objects

`ml.search` accepts structured, CTS and combined JSON dictionaries as well as
our Python query objects. Keep the native root member: `query` for structured
JSON, `ctsquery` for CTS JSON, or `search` for a combined query. The service
wraps standalone structured or CTS JSON in a combined request and applies the
same service and operation scopes as for Python objects.

```python
with MLClient() as ml:
    structured_documents = ml.search.documents(
        {
            "query": {"term-query": {"text": "coffee"}},
        }
    )
    cts_documents = ml.search.documents(
        {
            "ctsquery": {"wordQuery": {"text": "coffee"}},
        }
    )
```

Use [sq][mlclient.search.sq] or
[cts][mlclient.xquery.Cts] when you want Python constructors and local
validation; use dictionaries when you already have native JSON. Both are sent
as `application/json`. Strings remain Search API text queries, not JSON or XML
source. See the lexicon restriction below for raw CTS JSON.

### Combined queries with options and text

Both structured and CTS queries accept `options=` and `qtext=` in
`to_combined_query()`. Options are inline members as a dictionary, without an
outer `options` wrapper, or a [SearchOptions][mlclient.search.options.SearchOptions]
composition built with [opt][mlclient.search.opt]. `qtext` is an additional Search API string query; MarkLogic ANDs it
with the structured or CTS query.

```python
from mlclient.search import opt, sq

options = opt.options(opt.word_constraint("title", sq.element("title")))
combined = sq.collection("reports").to_combined_query(
    options=options,
    qtext="title:coffee",
)

with MLClient() as ml:
    documents = ml.search.documents(combined)
```

`to_combined_query(options=..., qtext=...)` accepts an inline options dictionary
or a [SearchOptions][mlclient.search.options.SearchOptions] object, including the
result of `opt.options(...)`, for both structured and CTS queries.
It returns a fresh `{"search": {...}}` dictionary. Structured
queries go under `query` (wrapped in [Query][mlclient.search.structured.Query]
when needed), CTS queries under `ctsquery`, and `options` and `qtext` alongside
them inside `search`. Mutating the result does not change the query or supplied
options. Omitted or `None` settings are left out; explicit empty dictionaries
and empty strings are retained.

`ml.search` accepts this JSON combined query directly. Inline scope options
supply defaults; options in the combined query override matching members,
and options in the operation's `scope=SearchScope(...)` override both.
Each option member is replaced as a whole, including lists of constraints.
An operation scope with `options=None` clears all inline and installed options.
An installed options name replaces the selected name and travels in the URL;
MarkLogic merges its server-side definitions with the combined query's inline
options. Naming installed options does not replace inline members locally.

For lower-level requests, pass the same dictionary as the body of
`ml.rest.search.post()` or `ml.rest.values.post()`.

For lexicon operations (`values`, `tuples`, `aggregate`), raw CTS JSON, standalone or inside a combined query,
is rejected: `/v1/values` ignores that filter.
Pass a CTS query object with service options instead, so the service can send
the required `additional-query` XML. Combined structured queries work on both
search and lexicon endpoints.

## Structured queries

Build Search API queries with [`sq`][mlclient.search.sq] or classes from [`mlclient.search.structured`][mlclient.search.structured].
Wrap subqueries in [`Query`][mlclient.search.structured.Query] when passing them directly to the Search API.

### Builder

The [`sq` module][mlclient.search.sq] provides short constructor aliases and
composition functions. Names that conflict with Python keywords or builtins have
a trailing underscore: `and_`, `or_`, `not_`, and `range_`. Query classes retain their full
names, such as [`AndQuery`][mlclient.search.structured.AndQuery] and [`RangeQuery`][mlclient.search.structured.RangeQuery].

```python
from mlclient.search import sq

query = sq.query(
    sq.and_(
        sq.range_(sq.element("price"), 20, operator="GE", index_type="xs:int"),
        sq.term("blue"),
    )
)
json_query = query.serialize()
xml_query = query.serialize("xml")
```

Import it with `from mlclient.search import sq`, or import an individual function
with `from mlclient.search.sq import term`. Leaf factories accept the same
parameters as the corresponding classes because they are aliases of those
constructors; composition functions
`query`, `and_`, `or_`, and `near` accept positional subqueries.

### Structured serialization details

A query validates its arguments when it is built, so an invalid selector,
operator, fragment scope or value cardinality raises `ValueError` or `TypeError`
at construction, not later inside a search. Queries are immutable and hashable:
list arguments are stored as tuples, so `AndQuery([q])` equals `AndQuery((q,))`.

Both representations retain literal values, repeated criteria, target namespaces,
explicit zero and false options. JSON uses the Search API's native cardinality
and metadata representation, not the native CTS JSON grammar. Numeric options,
including geographic coordinates, distances and weights, must be finite in both
formats; range and value query values may be `INF`, `-INF` or `NaN` and remain
lexical text with their declared index type.

The model classes can also be constructed directly:

```python
from xml.etree.ElementTree import tostring

from mlclient.search.structured import (
    AndQuery,
    CollectionQuery,
    Element,
    Query,
    WordQuery,
)

query = Query(
    AndQuery(
        [
            CollectionQuery("reports"),
            WordQuery(Element("title"), "annual", options=["case-insensitive"]),
        ]
    )
)
xml = tostring(query.serialize("xml"), encoding="unicode")
```

Query values are XML text, not executable code. ElementTree escapes text and
attribute values during serialization. Namespace prefixes in the output do not
affect the query's meaning; the namespace URI identifies the Search API elements.

### XML and JSON document targets

Use [`Element`][mlclient.search.structured.Element] for XML elements, optionally with an [`Attribute`][mlclient.search.structured.Attribute] selector;
[`JsonProperty`][mlclient.search.structured.JsonProperty] for JSON properties; or [`Field`][mlclient.search.structured.Field] for configured database fields.
The query's XML format does not restrict it to XML documents. Do not mix
target kinds in one query.

```python
from mlclient.search import sq

xml_value = sq.value(sq.element("item"), "published", attribute=sq.attribute("status"))
json_number = sq.value(sq.json_property("count"), 7, node_type="number")
json_boolean = sq.value(sq.json_property("active"), True, node_type="boolean")
json_null = sq.value(sq.json_property("deleted"), "", node_type="null")
```

JSON value queries default to string matching on the server. Set `node_type`
explicitly for numbers, booleans, or null values. Word queries only match text.

### Composition and scope

Use [`AndQuery`][mlclient.search.structured.AndQuery], [`OrQuery`][mlclient.search.structured.OrQuery], [`AndNotQuery`][mlclient.search.structured.AndNotQuery], [`NotQuery`][mlclient.search.structured.NotQuery], [`NotInQuery`][mlclient.search.structured.NotInQuery],
[`NearQuery`][mlclient.search.structured.NearQuery], and [`BoostQuery`][mlclient.search.structured.BoostQuery] to compose subqueries. [`TrueQuery`][mlclient.search.structured.TrueQuery] matches all
fragments; [`FalseQuery`][mlclient.search.structured.FalseQuery] matches none. [`TermQuery`][mlclient.search.structured.TermQuery] searches the current scope,
whereas [`WordQuery`][mlclient.search.structured.WordQuery] and [`ValueQuery`][mlclient.search.structured.ValueQuery] select a specific location.

Use [`CollectionQuery`][mlclient.search.structured.CollectionQuery], [`DirectoryQuery`][mlclient.search.structured.DirectoryQuery], and [`DocumentQuery`][mlclient.search.structured.DocumentQuery] to restrict
document selection. [`ContainerQuery`][mlclient.search.structured.ContainerQuery] applies a subquery inside an XML element
or JSON property. [`DocumentFragmentQuery`][mlclient.search.structured.DocumentFragmentQuery], [`PropertiesFragmentQuery`][mlclient.search.structured.PropertiesFragmentQuery], and
[`LocksFragmentQuery`][mlclient.search.structured.LocksFragmentQuery] select the fragment kind.

Pass `None` for an optional setting when you want MarkLogic to use its default.
MLClient leaves that setting out of the serialized query. Values such as `False`
and `0` are explicit choices and are sent as supplied.

### Range queries

```python
from mlclient.search import sq

price = sq.range_(sq.element("price"), 20, operator="GE", index_type="xs:decimal")
path = sq.range_(
    sq.path_index(
        "/r:report/r:price", namespaces={"r": "https://example.com/example/reports"}
    ),
    20,
    operator="GE",
    index_type="xs:decimal",
)
```

The database must have matching range indexes. Local serialization cannot
verify database indexes, fields, or configured query options. MarkLogic resolves
those when it executes the query. Operators use the Search API spellings
`LT`, `LE`, `GT`, `GE`, `EQ`, and `NE`.
Supply at least one value. Multiple values are supported only with `EQ` and
`NE`; MarkLogic otherwise discards the invalid condition with a query warning.

### Named constraints

Named constraints refer to definitions supplied in Search API options, rather
than embedding their target elements, properties, fields, or indexes:

```python
from mlclient.search import sq

query = sq.query(
    sq.and_(
        sq.range_constraint("price", 20, operator="GE"),
        sq.word_constraint("title", "blue"),
    )
)
xml = query.serialize("xml")
```

Build the corresponding options with
[SearchOptions][mlclient.search.options.SearchOptions] and run the query with
them:

```python
from mlclient import MLClient
from mlclient.search import opt, sq

options = opt.options(
    opt.range_constraint(
        "price",
        opt.range_(sq.element("price"), "xs:decimal"),
        facet=False,
    ),
    opt.word_constraint("title", sq.element("title")),
)

with MLClient() as ml:
    documents = ml.search(options=options).documents(query)
```

Use [opt][mlclient.search.opt] to compose range, word,
value, collection and container options. For other native option kinds, use
`opt.native(...)` with matching JSON and XML; see [Search options](#search-options).

Collection, container, properties, custom, value, word, and range constraint
builders are supported. A custom constraint delegates to its configured
server-side parser. [`ElementConstraintQuery`][mlclient.search.structured.ElementConstraintQuery] represents MarkLogic's deprecated
element constraint syntax; prefer [`ContainerConstraintQuery`][mlclient.search.structured.ContainerConstraintQuery] for new queries.
[`OperatorState`][mlclient.search.structured.OperatorState] selects a named operator state in the supplied options.

[`ValueConstraintQuery`][mlclient.search.structured.ValueConstraintQuery] writes values as XML `text` children. For JSON property
constraints, configure `<value type="number">`, `type="boolean"`, or
`type="null"` in options. Numbers and booleans are serialized using their XML
lexical forms. For null, omit the values and configure `type="null"`.
The local builder does not resolve or validate named constraint definitions.

Each constraint query accepts one non-empty constraint name. To match either
of two named constraints, combine separate builders with [`OrQuery`][mlclient.search.structured.OrQuery]. Although
the native documentation describes repeated constraint names, on the tested
versions MarkLogic resolves them as a singleton and rejects multiple names.

Geospatial and temporal query classes also have corresponding builder factories,
including `geo_element`, `geo_path`, `period_range`, and `period_compare`.

For the complete native syntax and semantics, see the official
[structured-query reference](https://docs.progress.com/bundle/marklogic-server-use-search-12/page/topics/structured-query.html).

## Search options

Build options by nesting immutable components, just as `sq` composes query
objects. The [opt module][mlclient.search.opt] provides factories using
the signatures of their corresponding classes. For example,
`opt.word_constraint(...)` constructs a
[WordConstraint][mlclient.search.options.WordConstraint], and
`opt.options(...)` constructs [SearchOptions][mlclient.search.options.SearchOptions].
Use [Range][mlclient.search.options.Range] or `opt.range_(...)` for an index target.

Selectors such as [sq.element][mlclient.search.structured.Element],
[sq.json_property][mlclient.search.structured.JsonProperty] and
[sq.field][mlclient.search.structured.Field] also describe targets in search
options. Although they come from the structured-query namespace, options built
with them work with structured queries, CTS queries and text queries alike.
For example, a CTS collection filter can be combined with a text constraint
whose target is defined by `sq.element()`:

```python
from mlclient import MLClient
from mlclient.search import opt, sq
from mlclient.xquery import cts

options = opt.options(opt.word_constraint("title", sq.element("title")))
combined = cts.collection_query("reports").to_combined_query(
    options=options,
    qtext="title:coffee",
)

with MLClient() as ml:
    documents = ml.search.documents(combined)
```

CTS index references and CTS query constructors are not option target selectors;
use `sq` selectors or their corresponding classes when defining these options.

```python
from mlclient.search import opt, sq

base = opt.options(
    opt.word_constraint("title", sq.element("title")),
    opt.page_length(10),
)
custom = opt.options(base, opt.page_length(20), opt.return_facets(False))

# base still requests 10 results; custom requests 20.
with MLClient() as ml:
    documents = ml.search(options=custom).documents("title:coffee")
```

Each group keeps its components in order. Repeatable options, such as
constraints, values, tuples and sort keys, accumulate. A later non-repeatable
option, such as page length, replaces an earlier one. Neither composition nor
serialization changes the original group. JSON and XML are built independently
and returned as fresh representations.

The class API is equivalent and has the same typed parameters:

```python
from mlclient.search.options import PageLength, SearchOptions, WordConstraint
from mlclient.search.structured import Element

options = SearchOptions(
    WordConstraint("title", Element("title")),
    PageLength(20),
)
```

[opt.page_length][mlclient.search.options.PageLength] requires a positive integer;
[opt.return_facets][mlclient.search.options.ReturnFacets] requires a boolean.
Use [opt.control][mlclient.search.options.Control] for other native scalar
options, such as `opt.control("quality-weight", 0.5)`.

For an option without a typed constructor, [opt.native][mlclient.search.options.NativeOptions]
accepts the same option in both native formats. Its result is an immutable group
that can be nested in `opt.options(...)`; neither format is inferred from the other:

```python
from xml.etree.ElementTree import Element

from mlclient.search import opt
from mlclient.search.structured import SEARCH_NS_URI

metrics = Element(f"{{{SEARCH_NS_URI}}}return-metrics")
metrics.text = "false"
options = opt.options(
    opt.page_length(20),
    opt.native({"return-metrics": False}, metrics),
)
```

## CTS queries

CTS query constructors return concrete subclasses of [`CtsQuery`][mlclient.xquery.CtsQuery], exported by
[`mlclient.xquery`][mlclient.xquery] like the structured vocabulary is by
[`mlclient.search.structured`][mlclient.search.structured]: logical,
selector, fragment and scope queries, word, value and range queries on text,
elements, attributes, fields, JSON properties and paths, geospatial queries,
temporal (`period_compare_query`, `period_range_query`, `lsqt_query`),
timestamp (`after_query`, `before_query`) and registered queries. These objects
retain the existing XQuery compilation behavior and also serialize independently
to native CTS JSON or XML:

```python
from mlclient.xquery import cts

query = cts.and_query(
    [
        cts.collection_query("reports"),
        cts.word_query("blue", options=["lang=en", "unstemmed"]),
    ]
)
json_query = query.serialize()
xml_query = query.serialize("xml")
code, variables = query.compile()
```

CTS JSON is **not** Search API structured JSON; its member names and
representation follow native CTS serialization. [`CtsQuery`][mlclient.xquery.CtsQuery] additionally
implements [`XqyExpression`][mlclient.xquery.XqyExpression], so the same query also compiles to XQuery.

### Compile and execute CTS queries

`compile()` returns XQuery source and bound variables without making a request.
Pass the query to a CTS expression evaluated by `ml.eval.expression()`, or to
`CtsService.search()` for hits with scores:

```python
from mlclient import MLClient
from mlclient.services import CtsService
from mlclient.xquery import cts

query = cts.and_query(
    [
        cts.collection_query("reports"),
        cts.word_query("blue"),
    ]
)
code, variables = query.compile()

with MLClient() as ml:
    documents = ml.eval.expression(cts.search(query=query))
    hits = CtsService(ml.rest).search(query=query)
```

Each execution makes a separate request. Structured queries do not implement
`compile()` and cannot be passed to XQuery evaluation or [`CtsService`][mlclient.services.CtsService].
See [XQuery API](xquery-api.md#choose-execution-or-composition) for composing
CTS under other functions.

### Local CTS serialization and limitations

Local serialization describes the query you built, leaving database-dependent
interpretation to MarkLogic. For example, when you omit `lang=`, the serialized
query leaves the language unspecified so the destination database can supply
its default. Options such as `exact` and query weights are also passed through
for MarkLogic to interpret when it reads the query.

For `cts.near_query()`, MLClient normalizes distances and `minimum-distance`
options as MarkLogic's constructor does. Very large distances can still produce
XML that `cts:query` rejects: the constructor can emit values above the signed
32-bit range accepted by the XML reader. Local serialization retains the
constructor's representation, so such a query can fail when sent to the server.

A serialized field query identifies its field by name. Run it against a database
where that field is configured; the name alone is not enough to reconstruct the
query in another database.

Arbitrary expressions remain compilable, but local serialization rejects
arguments that require server evaluation with `TypeError`. Arguments are
serializable when they are literals or these builders:

| Argument | Serializable forms |
| --- | --- |
| QNames | Unprefixed names (`"title"`) and `fn.qname(uri, name)`. A prefixed name such as `"t:title"` needs the compilation's namespace bindings, so use `fn.qname`. |
| Range and JSON values | Python literals: `str`, `int`, `Decimal`, `float`, `bool`, `date`, `datetime` (JSON property values support only strings, numbers and booleans). |
| Regions | `cts.point(latitude, longitude)`, `cts.box`, `cts.circle` and `cts.polygon` of such points. |
| Periods | `cts.period(start, end)` with literal start and end. |
| Range references | Element, element-attribute, field, JSON-property and path references with an explicit `type=` option; URI, collection and IRI references. String collations must match the destination index. |
| Region references | `cts.geospatial_region_path_reference` with an explicit `coordinate-system=` option. Precision, units and invalid-value settings are retained. |
| RDF values | Atomic literals and `FunctionCall("sem:iri", (uri,))`. Other semantic-value constructors require evaluation. |
| Model nodes | Python `dict`, `Element` or `ElementTree`, including sequences of them. Literal `xdmp.unquote(source)` is also supported. |

Atomic value arguments must be ready-to-use Python literals. Local serialization
preserves their types, including `xsi:type` in range-query XML and datatype
attributes for RDF literals. It does not evaluate function calls in these values,
including `xs.*` casts represented as [`FunctionCall`][mlclient.xquery.FunctionCall] and `cts.uris()`:
`to_json()`, `to_xml()` and
`to_combined_query()` raise `TypeError`. Such queries still compile to XQuery
and can be evaluated explicitly on the server. Use `1` instead of
`xs.integer(1.9)`, or `date(2026, 1, 1)` instead of `xs.date("2026-01-01")`,
when the result is already known and local serialization is needed.
An `xs.*` builder may return a literal directly when its input already has the
requested type (for example, `xs.double(1.5)`); that literal remains serializable.
QName, region and other explicitly supported builders listed above retain their
specialized serialization rules.

Path expressions are serialized as written. MarkLogic resolves their prefixes
where it reads the query, so prefer unprefixed paths or prefixes configured as
database path namespaces. MarkLogic cannot read a namespaced
`document_root_query` QName back from XML, even from its own constructor
output; use the JSON form for that query. Conversely, MarkLogic cannot read an
element-attribute reference back from its own JSON form, so `to_json()` raises
`TypeError` for it and `ml.search`, which sends JSON, cannot run it; use
`to_xml()` or run the query through eval.

All 54 query constructors return concrete [`CtsQuery`][mlclient.xquery.CtsQuery] subclasses, including
`range_query`, `geospatial_region_query`, `column_range_query`,
`triple_range_query`, `reverse_query` and `similar_query`. Pass a serializable
CTS query to [`ml.search`](../guides/search.md) to run it without evaluating XQuery.
`cts.parse()` and `cts.query()` instead return [`RuntimeQuery`][mlclient.xquery.RuntimeQuery]: their concrete
native query depends on server evaluation. They compose and compile normally,
but local JSON/XML serialization raises `TypeError`, including when nested in
another query. Evaluate them explicitly with `ml.eval.expression()` when needed.
Reference namespace maps have no native serialized representation; use EQNames
in reference paths or destination database path namespaces instead.

#### Column range queries

`column_range_query` can be serialized locally when you supply its TDE column ID
with `with_column_id()`. Use an ID already stored in your application's
configuration for the destination database and column:

```python
from mlclient.xquery import cts

# Example configured ID; use the ID for your destination's reports.items.price.
column_id = 11548423394257569743
query = cts.column_range_query("reports", "items", "price", 2)
query = query.with_column_id(column_id)
native_json = query.to_json()
native_xml = query.to_xml()
```

This is a limitation of native CTS serialization: MarkLogic represents the
column query as a `triple-range-query` whose predicate includes `columnID`.
Schema, view and column names alone are insufficient to reconstruct that query
from JSON/XML. Without the ID, local serialization raises `TypeError`.
Compilation still uses the names and requires no ID; the library never fetches
metadata implicitly.

If the ID is not already known, obtain it from the server. The documented
[`sql:columnID`](https://docs.marklogic.com/sql:columnID) function avoids
extracting it from a query's XML. An explicit eval request can return it as a
Python integer:

```python
from mlclient import MLClient
from mlclient.xquery import cts

with MLClient() as ml:
    # Requires the reports.items view and its indexed price column.
    column_id = ml.eval.xquery(
        'sql:columnID("reports", "items", "price") => xs:integer()'
    )
    query = cts.column_range_query("reports", "items", "price", 2)
    query = query.with_column_id(column_id)
    native_json = query.to_json()
    native_xml = query.to_xml()
```

This adds a server request before serialization. For a one-off search, it is
usually simpler to execute the column query directly through [`CtsService`][mlclient.services.CtsService] or
`ml.eval.expression()` (using an unfiltered `cts.search` or `cts.uris`) and let
MarkLogic resolve the column. Explicit IDs remain available when you need to
build or reuse a serialized REST query.

#### Similar queries

`cts.similar_query()` finds documents similar to a supplied example document.
That example is the query's **model document**.

**For a JSON model document, serialize the query as JSON.** On the tested
versions, reading the query back from XML turns its JSON
model into text. The query may still be accepted, but its input no longer has
the original JSON type. This also happens with XML produced by MarkLogic itself.

```python
from mlclient.xquery import cts

model = {
    "title": "Coffee brewing",
    "text": "Freshly ground coffee beans",
}
query = cts.similar_query(model)
native_json = query.to_json()  # Preserves the model as a JSON object.
```

The Python dictionary supplies the model directly. Building and serializing
the query sends no request; no `xdmp.unquote()` wrapper is needed.
`query.to_xml()` produces the native XML shape, but cannot prevent MarkLogic from
reading the embedded JSON model as text.

Choose the execution route according to the model:

| Model document | Recommended route |
| --- | --- |
| Literal JSON | `to_json()` or `ml.search`, which sends JSON. |
| Literal XML | Either `to_json()` or `to_xml()` preserves the model. |
| An expression such as `fn.doc("/example.json")` | Execute through `ml.eval.expression()` or [`CtsService`][mlclient.services.CtsService]; local serialization raises `TypeError`. |

Direct execution through eval or [`CtsService`][mlclient.services.CtsService] also avoids the XML round-trip for
a JSON model. We have no verified workaround that preserves a JSON model when
the query is sent as XML.

Similarity options are a separate concern. Pass a Python XML `Element` in the
`cts:distinctive-terms` namespace:

```python
from xml.etree.ElementTree import fromstring

options = fromstring(
    '<options xmlns="cts:distinctive-terms"><max-terms>20</max-terms></options>'
)
query = cts.similar_query(model, options=options)
```

Local JSON serialization supports `score`, `max-terms`, `min-val`, `min-weight`
and `complete`. Unrecognized literal options raise `ValueError`; options that
must be fetched or computed on the server require explicit evaluation.

#### XML models and preservation limits

For an XML model, pass an `Element` or an `ElementTree` directly:

```python
from xml.etree.ElementTree import ElementTree, fromstring
from mlclient.xquery import cts

root = fromstring("<article><title>Coffee brewing</title></article>")
query = cts.similar_query(root)  # An XML element as the model.
document_query = cts.similar_query(ElementTree(root))  # An XML document instead.
native_xml = query.to_xml()
```

Serialization preserves the supplied XML content and namespace URIs. Python's
XML parser may already have dropped comments or processing instructions; mlclient
cannot restore them. Namespace prefixes may change during Python XML conversion.
The element's tail (text after its closing tag) is outside the supplied node and
is omitted.

If you already have literal XML text, `xdmp.unquote(source)` remains available.
For this form, local CTS serialization also retains comments, processing
instructions and namespace declarations present in the text. Two special cases
require care:

- **XML with a DTD:** local serialization raises `TypeError`. Execute the query
  through `ml.eval.expression()` or [`CtsService`][mlclient.services.CtsService] so MarkLogic parses the document.
- **Literal XML using prefixes such as `ns0`:** JSON serialization works, but XML
  serialization raises `TypeError` because ElementTree reserves those prefixes.
  Use another prefix or execute the query directly. This restriction does not
  apply to Python XML nodes: their generated prefixes are converted automatically.
