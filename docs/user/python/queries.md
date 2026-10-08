# Structured and CTS queries

Choose a query vocabulary, then use the same API to serialize and search:

| | Structured queries | CTS queries |
| --- | --- | --- |
| Builder | `sq` from `mlclient.search.structured` | `cts` from `mlclient.xquery` |
| Native format | Search API structured JSON/XML | CTS JSON/XML |
| Local serialization | `serialize()`, `to_json()`, `to_xml()` | `serialize()`, `to_json()`, `to_xml()` |
| Combined query | `to_combined_query()` under `query` | `to_combined_query()` under `ctsquery` |
| REST execution | `ml.search` | `ml.search` |
| XQuery compilation and execution | Not supported | `compile()`, `ml.eval.expression()`, `CtsService` |

## Shared serialization API

Both families implement `mlclient.search.QueryComponent` and
`mlclient.search.SearchQuery`. The API is shared; their native wire formats
remain distinct. Build equivalent queries with either vocabulary:

```python
from xml.etree.ElementTree import tostring

from mlclient.search.structured import sq
from mlclient.xquery import cts

structured = sq.query(sq.and_(sq.collection("reports"), sq.term("blue")))
native = cts.and_query([
    cts.collection_query("reports"),
    cts.word_query("blue"),
])

for query in (structured, native):
    json_query = query.serialize()       # Same as serialize("json") or to_json().
    xml_query = query.serialize("xml")   # Same as to_xml(); an ElementTree element.
    xml_text = tostring(xml_query, encoding="unicode")
    combined = query.to_combined_query()
```

Serialization runs locally and sends no request. JSON results are fresh
JSON-compatible dictionaries; XML results are fresh ElementTree elements.
Changing either result does not change the query. JSON and XML are built
independently, rather than converting through the other format.
XML output uses the conventional `search` and `cts` namespace prefixes; the
namespace URI, rather than its prefix, identifies each vocabulary.

## Execute over REST

[`ml.search`](search.md) accepts both query families and serializes them locally:

```python
from mlclient import MLClient

with MLClient() as ml:
    structured_documents = ml.search.documents(structured)
    cts_documents = ml.search.documents(native)
```

For lower-level requests, `to_combined_query()` produces `{"search": {...}}`,
placing structured queries under `query` (wrapped in `Query` when needed) and
CTS queries under `ctsquery`. Add `qtext` or `options` to the inner dictionary
and pass it as the body of `ml.rest.search.post()` or `ml.rest.values.post()`.
MarkLogic accepts combined queries only in POST requests.

## Structured queries

Build Search API queries with `sq` or classes from `mlclient.search.structured`.
Wrap subqueries in `Query` when passing them directly to the Search API.

### Builder

The stateless `sq` builder uses short factory names. Python keywords have a
trailing underscore: `and_`, `or_`, and `not_`. Query classes retain their full
names, such as `AndQuery` and `RangeQuery`.

```python
from mlclient.search.structured import sq

query = sq.query(
    sq.and_(
        sq.range(sq.element("price"), 20, operator="GE", index_type="xs:int"),
        sq.term("blue"),
    )
)
json_query = query.serialize()
xml_query = query.serialize("xml")
```

Use `StructuredQueryBuilder()` to create another builder. Leaf factories accept
the same parameters as the corresponding classes; composition factories
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
    AndQuery([
        CollectionQuery("reports"),
        WordQuery(Element("title"), "annual", options=["case-insensitive"]),
    ])
)
xml = tostring(query.serialize("xml"), encoding="unicode")
```

Query values are XML text, not executable code. ElementTree escapes text and
attribute values during serialization. Namespace prefixes in the output do not
affect the query's meaning; the namespace URI identifies the Search API elements.

### XML and JSON document targets

Use `Element` for XML elements, optionally with an `Attribute` selector;
`JsonProperty` for JSON properties; or `Field` for configured database fields.
The query's XML format does not restrict it to XML documents. Do not mix
target kinds in one query.

```python
from mlclient.search.structured import Attribute, Element, JsonProperty, ValueQuery

xml_value = ValueQuery(Element("item"), "published", attribute=Attribute("status"))
json_number = ValueQuery(JsonProperty("count"), 7, node_type="number")
json_boolean = ValueQuery(JsonProperty("active"), True, node_type="boolean")
json_null = ValueQuery(JsonProperty("deleted"), "", node_type="null")
```

JSON value queries default to string matching on the server. Set `node_type`
explicitly for numbers, booleans, or null values. Word queries only match text.

### Composition and scope

Use `AndQuery`, `OrQuery`, `AndNotQuery`, `NotQuery`, `NotInQuery`,
`NearQuery`, and `BoostQuery` to compose subqueries. `TrueQuery` matches all
fragments; `FalseQuery` matches none. `TermQuery` searches the current scope,
whereas `WordQuery` and `ValueQuery` select a specific location.

Use `CollectionQuery`, `DirectoryQuery`, and `DocumentQuery` to restrict
document selection. `ContainerQuery` applies a subquery inside an XML element
or JSON property. `DocumentFragmentQuery`, `PropertiesFragmentQuery`, and
`LocksFragmentQuery` select the fragment kind.

Optional parameters set to `None` are omitted, leaving MarkLogic's defaults
intact. Explicit `False` and zero values are retained. Directory URIs must end
with `/`; an omitted `infinite` uses the server's recursive default.

### Range queries

```python
from mlclient.search.structured import Element, PathIndex, RangeQuery

price = RangeQuery(Element("price"), 20, operator="GE", index_type="xs:decimal")
path = RangeQuery(
    PathIndex("/r:report/r:price", namespaces={"r": "urn:example:reports"}),
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
from mlclient.search.structured import (
    AndQuery,
    Query,
    RangeConstraintQuery,
    WordConstraintQuery,
)

query = Query(
    AndQuery([
        RangeConstraintQuery("price", 20, operator="GE"),
        WordConstraintQuery("title", "blue"),
    ])
)
xml = query.serialize("xml")
```

Build the corresponding options with
[SearchOptions][mlclient.search.options.SearchOptions] and run the query with
them:

```python
from mlclient import MLClient
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

options = (
    SearchOptions()
    .range_constraint("price", Range(Element("price"), "xs:decimal"), facet=False)
    .word_constraint("title", Element("title"))
)

with MLClient() as ml:
    documents = ml.search(options=options).documents(query)
```

`SearchOptions` builds range, word, value, collection and container
constraints; define other kinds with `add()`.

Collection, container, properties, custom, value, word, and range constraint
builders are supported. A custom constraint delegates to its configured
server-side parser. `ElementConstraintQuery` represents MarkLogic's deprecated
element constraint syntax; prefer `ContainerConstraintQuery` for new queries.
`OperatorState` selects a named operator state in the supplied options.

`ValueConstraintQuery` writes values as XML `text` children. For JSON property
constraints, configure `<value type="number">`, `type="boolean"`, or
`type="null"` in options. Numbers and booleans are serialized using their XML
lexical forms. For null, omit the values and configure `type="null"`.
The local builder does not resolve or validate named constraint definitions.

Each constraint query accepts one non-empty constraint name. To match either
of two named constraints, combine separate builders with `OrQuery`. Although
the native documentation describes repeated constraint names, on the tested
versions MarkLogic resolves them as a singleton and rejects multiple names.

Geospatial and temporal query classes also have corresponding builder factories,
including `geo_element`, `geo_path`, `period_range`, and `period_compare`.

For the complete native syntax and semantics, see the official
[structured-query reference](https://docs.progress.com/bundle/marklogic-server-use-search-12/page/topics/structured-query.html).

## CTS queries

CTS query constructors return concrete subclasses of `CtsQuery`, exported by
`mlclient.xquery` like the structured vocabulary is by
`mlclient.search.structured`: logical,
selector, fragment and scope queries, word, value and range queries on text,
elements, attributes, fields, JSON properties and paths, geospatial queries,
temporal (`period_compare_query`, `period_range_query`, `lsqt_query`),
timestamp (`after_query`, `before_query`) and registered queries. These objects
retain the existing XQuery compilation behavior and also serialize independently
to native CTS JSON or XML:

```python
from mlclient.xquery import cts

query = cts.and_query([
    cts.collection_query("reports"),
    cts.word_query("blue", options=["lang=en", "unstemmed"]),
])
json_query = query.serialize()
xml_query = query.serialize("xml")
code, variables = query.compile()
```

CTS JSON is **not** Search API structured JSON; its member names and
representation follow native CTS serialization. `CtsQuery` additionally
implements `XqyExpression`, so the same query also compiles to XQuery.

### Compile and execute CTS queries

`compile()` returns XQuery source and bound variables without making a request.
Pass the query to a CTS expression evaluated by `ml.eval.expression()`, or to
`CtsService.search()` for hits with scores:

```python
from mlclient import MLClient
from mlclient.services import CtsService
from mlclient.xquery import cts

query = cts.and_query([
    cts.collection_query("reports"),
    cts.word_query("blue"),
])
code, variables = query.compile()

with MLClient() as ml:
    documents = ml.eval.expression(cts.search(query=query))
    hits = CtsService(ml.rest).search(query=query)
```

Each execution makes a separate request. Structured queries do not implement
`compile()` and cannot be passed to XQuery evaluation or `CtsService`.
See [XQuery API](xquery-api.md#choose-execution-or-composition) for composing
CTS under other functions.

### Local CTS serialization and limitations

Serialization keeps the arguments you supplied: options stay in their order,
`exact` is not expanded, an omitted `lang=` stays omitted and weights are not
clamped. MarkLogic applies those normalizations, including the database
language, when it reads the serialized query, so it reconstructs the same query
as the native constructor. Near-query serialization still applies native
distance rounding and minimum-distance normalization. Native constructors can
emit distances above the signed 32-bit range that `cts:query` itself rejects
when reading XML; local serialization retains that representation rather than
hiding the server limitation. Reconstructing field queries also requires the
referenced field to exist in the destination database.

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
including `xs.*` casts represented as `FunctionCall` and `cts.uris()`:
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

All 54 query constructors return concrete `CtsQuery` subclasses, including
`range_query`, `geospatial_region_query`, `column_range_query`,
`triple_range_query`, `reverse_query` and `similar_query`. Pass a serializable
CTS query to [`ml.search`](search.md) to run it without evaluating XQuery.
`cts.parse()` and `cts.query()` instead return `RuntimeQuery`: their concrete
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
usually simpler to execute the column query directly through `CtsService` or
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
| An expression such as `fn.doc("/example.json")` | Execute through `ml.eval.expression()` or `CtsService`; local serialization raises `TypeError`. |

Direct execution through eval or `CtsService` also avoids the XML round-trip for
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
  through `ml.eval.expression()` or `CtsService` so MarkLogic parses the document.
- **Literal XML using prefixes such as `ns0`:** JSON serialization works, but XML
  serialization raises `TypeError` because ElementTree reserves those prefixes.
  Use another prefix or execute the query directly. This restriction does not
  apply to Python XML nodes: their generated prefixes are converted automatically.
