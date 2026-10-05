# Index-aware search

## Discover before choosing a query

1. Identify the content database behind the chosen REST connection.
2. In an ml-gradle project, inspect `ml-config/databases/*.json` and relevant
   environment overrides; check namespace bindings, range index definitions,
   fields, URI/collection lexicons, word positions and TDE configuration.
3. Read deployed properties with
   `ml.manage.databases.get_properties('Documents', data_format='json')` and
   check the status. Local configuration describes intent, not necessarily live
   state. Use `/manage/v2/databases/{name}?view=describe-indexes` or
   `/v1/config/indexes` for the documented additional view (raw fallback).
4. Match QName/property/path, scalar type, collation and index options exactly.
   Confirm indexing/reindexing is complete. Do not create an index without an
   explicit requested configuration change.
5. Choose a collection/directory/root constraint and return the smallest needed
   shape: estimate → URIs → indexed values → projected nodes → full documents.

```sh
ml http get /manage/v2/databases/Documents/properties -c manage format=json -e dev
ml http get /manage/v2/databases/Documents -c manage view=describe-indexes format=json -e dev
ml http get /v1/config/indexes -c content -e dev
```

## Use builders and services

```python
from mlclient.services import AsyncCtsService

# Within one open AsyncMLClient:
cts = AsyncCtsService(ml.rest)
query = cts.and_query([
    cts.collection_query('products'),
    cts.word_query('coffee'),
])
hits = await cts.search(query=query, pos=[1, 25], options=['filtered'])
uris = await cts.uris(query=query, pos=[1, 25])
estimate = await cts.estimate(query=query)
```

Builders construct expressions without I/O; service execution methods await
HTTP and parse results. `CtsService` is the sync counterpart. Pure builders also
live under `mlclient.functions.xqy` (`cts`, `fn`, `xdmp`, `xs`, `xpath`), executed
with `ml.eval.expression`. Do not invent a `.cts` client property.
Search returns `list[SearchHit]` with content, score, source_uri/source_path.
URIs return strings, indexed values return `ValueHit` with value/frequency.
Selection is one-based and inclusive: `pos=[1,25]`, next page `[26,50]`.

For namespaced XML:

```python
cts = AsyncCtsService(ml.rest, namespaces={'p': 'urn:products'})
hits = await cts.search(
    expression='/p:catalog/p:product', query=cts.word_query('coffee'),
    xpath='p:title', pos=[1, 10],
)
```

`expression` sets the searchable subtree. `xpath` projects from selected hits
AFTER pagination; it can return zero or several nodes per hit. `hit.xpath` runs
locally on already-returned XML. Do not confuse those three operations. Keep
filtering enabled for nested paths; document-fragment matching alone can include
siblings that fail the predicate.

## Choose index-only operations carefully

- URI/collection lexicons enable `cts:uris`, URI matching and collection enumeration.
- Range queries, values, index ordering and aggregates require the corresponding
  range index. Match numeric/date types and string collation explicitly.
- Fields are useful for scoped text search when the project's field definition
  actually matches the intended text. Missing required field/range indexes raise
  errors; missing positions or value-search optimizations can instead increase
  filtering cost. Inspect rather than assuming all flags must be enabled.
- Prefer a single query with a value sequence (implicit OR where the constructor
  supports it), or `cts:or-query`; summing separate counts can double-count hits.
- Lexicon `cts:frequency` reflects fragment/item frequency options, not arbitrary
  nested-node cardinality. `cts:estimate` counts index candidates, and URI/lexicon
  query filters can still overmatch where fragment semantics are insufficient.
- For exact counts, filter at the correct scope and count matched results. This
  costs more; label estimates honestly instead of silently substituting them.

```python
reference = cts.json_property_reference('price')
values = await cts.values(reference, query=query, pos=[1, 20])
total = await cts.sum_aggregate(reference, query=query)
```

Check the actual `.values`/aggregate signatures in the installed version. Use
`cts.element_reference` with a declared namespace for XML, `.path_reference` for
configured paths, and `.field_reference` for configured field indexes. Declare
reference collation/type options when needed to select the intended index.

## Correctness before optimization

Use `cts:search(/invoice, $query)` for a known unqualified XML root. A namespaced
root needs an explicit prefix. For dynamic root constraints on MarkLogic 11+,
use `cts:document-root-query(fn:QName($namespace, $local-name))`; verify availability
on the target version. On 10, use a static searchable XPath when possible or
apply a correct filtered root predicate. `cts:element-query` means an element
anywhere in the fragment; it is not equivalent to document-root matching.

Use filtered search by default. Choose unfiltered only after showing the chosen
indexes and fragment model resolve the full predicate without false positives.
For stable pages, include an explicit deterministic order/tie-breaker. Deep
positional pages can repeatedly scan preceding results; avoid assuming constant
page cost. Concurrent pages can observe different snapshots if content changes.

Index ordering can be lost after a path step across a node sequence. Preserve
original order with the simple map operator `!` for per-hit projections, or
explicit FLWOR ordering. Do not sort a million Python documents to replace a
server range-index sort. Prefer aggregate/lexicon results or Optic for analytics
where project TDE views exist; raw `/v1/rows` is available through HTTP.

Measure representative queries with `xdmp:plan`, `xdmp:query-meters`, and optional
query tracing/profiling. Compare results as well as timing; never promote a
project-specific benchmark into a universal speed claim.

Docs: [search](https://monasticus.github.io/mlclient/user/python/search/),
[XQuery builders](https://monasticus.github.io/mlclient/user/python/xquery-api/),
[MarkLogic cts:search](https://docs.marklogic.com/12.0/cts:search),
[cts:values](https://docs.marklogic.com/12.0/cts:values),
[query performance](https://docs.marklogic.com/guide/performance).

For operation selection and fragment correlation see [query planning](query-planning.md).
For native URI cursor/file exports see [URI workflows](uri-workflows.md).
For Python-only composition see [builders](python-builders.md).
