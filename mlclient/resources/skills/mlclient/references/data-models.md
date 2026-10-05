# Choose a MarkLogic model and execution route

Use existing project models and endpoints first. SQL, Optic, RDF and temporal
features do not imply dedicated MLClient methods exist: native files via eval
and documented raw REST are appropriate fallbacks.


| Need | Route through MLClient | Check before using |
| --- | --- | --- |
| Search API snippets, facets, constraints and saved options | Raw REST `/v1/search`, `/v1/config/query` contracts | Search option names, constraint indexes, pagination, response format |
| Relational joins and grouped rows over documents | Eval XQuery/SJS importing Optic; REST rows endpoints when appropriate | Deployed TDE schema/view/columns, join keys, duplicate and null semantics |
| RDF graph queries | REST SPARQL/graphs endpoints or eval `sem` functions | Graph permissions, default/named graph scope, query vs update |
| Temporal document operations | REST temporal/document contracts or temporal eval APIs | Temporal collection/axes, system/valid time and update restrictions |
| Geospatial queries | CTS geospatial builders where available, otherwise eval | Correct geo index, coordinate system, units and geometry type |
| Vector queries | Version-supported CTS/Optic/eval or REST contract | Server version, vector type/dimensions, distance and actual index availability |
| Application resource extensions | REST `/v1/resources/NAME` with `rs:` parameters | Extension signature, verbs, permissions and database bindings |
| Server transforms | REST transform/config contracts | Transform name, parameters, content format and update/read context |
| Schema/TDE inspection | Read schemas documents/configuration; eval targeted metadata | Content database's schemas association and deployment state |
| Backup/restore, forests and cluster operations | Named Manage APIs then complete endpoint fallback | Task status and completion, availability effects, privileges |
| Large data movement | MLClient bounded document batches for Python integration | Consider existing Flux/MLCP tooling for established bulk pipelines |

## TDE and Optic: rows, joins and aggregates

Template Driven Extraction maps XML/JSON document context nodes to rows with
schema/view/column identities and scalar types. Inspect the template's context,
collection restrictions, namespaces, optional columns and extraction expressions.
One document can produce many rows; row cardinality is not document cardinality.
Check the deployed template in the associated schemas database, not just a
source `ml-schemas/tde` file. Invalid extraction/type data and recent template
changes can explain missing rows or reindex work.

Use Optic when joining/grouping rows is clearer than fragment co-occurrence or
retrieving whole documents. In XQuery import:

```xquery
import module namespace op = "http://marklogic.com/optic"
  at "/MarkLogic/optic.xqy";
```

Build a plan with the appropriate source (`from-view`, search, lexicons, triples),
then row predicates, joins/projections/grouping/order and `result`. Use Optic
expression functions and explicit column references, not immediate language
comparisons evaluated while constructing the plan. Qualify columns when views
share names. Inner joins can multiply rows; left joins preserve unmatched rows
and introduce undefined values. Check existence/anti-join semantics when the
requirement is membership rather than adding columns.

Document-level CTS constraints and extracted-row predicates have different
semantics. Moving a condition across extraction or joins can change which rows
qualify. Fragment-ID joins can link rows to source documents when the chosen
source includes the necessary identifiers; fetch document content only when
needed. For totals verify nullable and multivalued inputs, grouping keys and
join multiplication before optimising execution.

Put an Optic main module in a `.xqy` file, bind its external inputs and invoke
`ml.eval.file`. Use REST rows/plan endpoints through named support or raw HTTP
when the contract fits. Do not invent `ml.optic` or Python plan methods. Native
reference: [Optic](https://docs.marklogic.com/guide/optic).

## RDF/SPARQL

Distinguish managed triples loaded through graph APIs from embedded triples
indexed in ordinary documents. Named/default graph selection, triple indexes,
permissions and inference rules determine what a query sees. A graph IRI is
not interchangeable with an arbitrary document URI or application collection.

Use `/v1/graphs/sparql` for SPARQL and graph endpoints for RDF data movement,
with supported RDF/result Content-Type and Accept headers. Check the matching
[REST contract](endpoints.md) before using query vs update verbs/bodies. Native
`sem:sparql` in a separate module is useful for composition with document logic.
Bind RDF inputs with correct IRI/literal/datatype/language-tag semantics; do not
assemble query text from Python user strings. A literal string and an IRI with
identical text are different RDF terms. Pagination without explicit ordering is
not a stable graph export. Inference can change results and execution cost.

## Temporal data

Temporal collections use configured time axes backed by the appropriate range
indexes. Valid time models business truth; system time models database history.
Read the project's axes, temporal collection definitions, latest-version and
URI-version conventions before querying or changing temporal documents.

Use temporal-specific document APIs; ordinary replacement/deletion is not a
substitute for version creation, correction, deletion or wiping all history.
LSQT and protected/WORM rules can limit what operations/time ranges are allowed.
Confirm whether the caller needs current state, state valid at a business time,
state known at a system time, or all versions. Use explicit timezone and interval
semantics and include them in reports.

## Geo, vectors, schemas and ingestion

For geospatial queries check index kind, coordinate system, coordinate order,
units and stored geometry representation. A geo region constructor and a geo
index reference are different objects. For vector search inspect the server
version, dimensions, vector scalar/index type and distance metric. Approximate
nearest-neighbour top-k is not an exact similarity threshold or a general CTS
word query. Verify index availability rather than treating a query's success
as proof it used an efficient index.

XML schema validity, JSON application validation and TDE extraction are separate
contracts. Existing envelope/entity models may split canonical data, headers,
attachments and instance payloads; query the intended layer. Inspect the actual
installed Entity Services/Data Hub modules and server version instead of assuming
all historical generator APIs are available.

For ingestion preserve document format, metadata/permissions/collections and
URI mapping. Existing transforms or REST resources can enforce domain rules.
Flux/MLCP pipelines can be appropriate for established bulk movement; XCC/XDBC
is a different protocol, not another port for MLClient HTTP. Python bounded
batching fits custom integrations where library control and per-item reports
matter. Reuse project deployment and ingestion tooling rather than rebuilding it.
