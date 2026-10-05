# Plan a query from the requested result

Read [index discovery](search.md) first. Query optimisation starts with the
correct database, data shape and security context, not extra parallel requests.

| Need | Operation | Required understanding |
| --- | --- | --- |
| Retrieve a known URI | Document service | Exact URI, permissions and content/metadata categories |
| Check an indexed condition exists | `xdmp:exists(searchable_path)` or bounded query | Searchable database expression versus already-loaded node |
| Approximate size | `cts:estimate(query)` | Fragment candidates, scope and index precision |
| Exact documents/subtrees | Filtered `cts:search` | Searchable root/subtree and query correlation |
| URI candidates | `cts:uris` | URI lexicon, document fragments and cursor flow |
| Distinct indexed values/facets | `cts:values` / value service | Range reference and frequency meaning |
| Correlated tuples | Value tuples/co-occurrences where appropriate | Fragment relationships are not arbitrary relational joins |
| Numeric aggregate | Indexed aggregate or Optic | Item/fragment frequency and multivalued data |
| Search UI snippets/facets/constraints | Search API / REST search | Named options, result format and constraints |
| Join rows across entities | Optic/TDE | Extracted row schema, join multiplicity and permissions |

## Match the index precisely

For range queries/references check scalar type, namespace, local name, collation
and the relevant element, attribute, JSON property, path or field. String values
must not accidentally compare as numbers or vice versa. Dates need a defined
timezone and range boundaries; use a half-open interval `[start, end)` for
adjacent time windows when that matches the business contract.

Value queries match indexed values; word queries match tokenised text under
word options. Exact whole-value matching, case sensitivity, stemming, punctuation,
wildcards and collation are different choices. Do not present a word query as
literal substring search. Scope full-text to the correct property/element/field
when a global word could match unrelated content.

A field's definition can include/exclude/weight parts of a document and contain
field-specific indexes. A range field query requires its field range index;
merely having a word field is insufficient. Path range indexes preserve the
chosen path and namespace bindings, not the visible project prefix spelling.

URI, collection, range-value and triple lexicons/indexes are distinct. A URI
index used for document lookup is not proof that the URI lexicon is enabled.
Inspect project database configuration and live Manage properties, including
reindex status, before calling lexicon functions.

## Fragments and correlation

Index resolution selects fragments; fragment scope may differ from documents
when custom fragmentation is configured. A query combining conditions can match
values in different sibling objects/line items in the same fragment. If both
conditions must apply to the **same** element, use an element-scoped query and
a filtered searchable subtree or another model that preserves that relationship.
For JSON arrays of objects, use an appropriate scoped strategy and verify on
counterexamples; an AND over two global properties does not imply same-object
correlation.

`cts:element-query` constrains descendants of an element; it does not mean that
this element is the document root. Use a known searchable root XPath or a
version-supported document-root query. A namespaced root must match its URI.
Version-check `cts:document-root-query` for servers before MarkLogic 11.

Negation also needs care: approximate index matches inside NOT can affect
correctness. Choose an index-resolvable exclusion or deliberately filtered
logic at the required scope. Test near/phrase positions, repeated values and
optional fields against actual data. `cts:contains` on a loaded node is useful
for local matching; it is not a universal replacement for full search filtering.

## Values, counts and aggregation

Lexicon values are distinct entries. Frequencies describe fragment or item
frequency under selected options; they are not automatically document counts,
array lengths or row counts. Values tuples/co-occurrences can relate values
within fragments without preserving a repeated nested element's row pairing.
Use TDE/Optic or explicit node-level processing for that requirement.

An indexed sum/average over multivalued data needs a defined frequency model.
Decide whether you mean one contribution per distinct indexed value, per fragment
or per occurrence. Validate against a small known dataset with duplicates and
missing values before trusting an aggregate. A filtered document count can cost
much more than an estimate: label the requested/returned metric explicitly.

## Order, pages and performance

Use explicit index ordering for sorted results where the matching range index
exists. Scoring is useful for relevance; choose `score-zero` when relevance is
irrelevant. Do not use arbitrary sorting flags to simulate an absent index.
Pagination by a nonunique sort key needs a tie-breaker; repeated live requests
can change pages when data changes. Do not confuse URI cursors with search offsets.

Apply a positional bound before projecting documents, preserve order with
simple-map/FLWOR operations, and return only data the caller needs. For broad
existence checks use a suitable index-based operation; wrapping a whole database
XPath in `fn:exists` or a count can materialize unnecessary results.

Inspect `xdmp:plan`, query meters and profiler output for suspected scans/filtering.
Measure equivalent results under the same data, permissions and cache/load
conditions. Include serialization/network/client cost in end-to-end timings.
An expensive query repeated concurrently can overload a server rather than
improve throughput. Use [URI workflows](uri-workflows.md) for large URI sets and
[data models](data-models.md) when document fragments do not fit the problem.
