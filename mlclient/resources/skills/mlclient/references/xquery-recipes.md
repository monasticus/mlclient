# Write XQuery that behaves as intended

Read [coding conventions](marklogic-code.md) for style. This reference addresses
semantics and common implementation decisions. Keep substantial native code in
`.xqy` files and execute with `ml eval file.xqy` / `ml.eval.file(path, variables=...)`.
Do not turn Python scripts into string generators for XQuery.

## Scope, cardinality and types

XML element identity is namespace URI plus local name, not the visible prefix.
`/order` does not select `/p:order`; declare the application namespace or use
`Q{urn:orders}order`. Attributes without prefixes have no namespace even when
an element uses a default namespace. Inspect actual node names instead of
using `local-name()` everywhere and losing namespace constraints.

Distinguish document nodes, root elements, nested elements, attributes, atomic
values, JSON object/array nodes and maps. `fn:doc($uri)` returns a document node;
extract the intended child before calling a function that expects an object.
Use `fn:base-uri`/`xdmp:node-uri` for source identity at the appropriate node;
an application `id` property is not automatically its database URI.

Declare intentional cardinality (`item()?`, `element(p:order)*`, `xs:string+`).
A type annotation checks a contract, not arbitrary implicit conversion. Cast
numeric/date input once at the boundary; use `castable as` when invalid data is
expected. Preserve absent values separately from zero, false and empty string.
Never apply numeric predicates such as `$items[0]` as a truth test: predicates
with numeric effective values select positions.

Function mapping in `1.0-ml` can invoke a singleton function for each member of
a sequence and invoke it zero times for `()`. Avoid relying on this implicitly
in API contracts; use explicit loops or `declare option xdmp:mapping "false";`
when strict cardinality is required. Audit legacy modules before changing that
option globally. Use `some`/`every` or `fn:exists` instead of an uncertain atomic
sequence's effective boolean value.

## Transform results without losing order

```xquery
xquery version "1.0-ml";
declare namespace p = "urn:orders";
declare variable $collection as xs:string external;
declare variable $status as xs:string external;
declare variable $size as xs:integer external;

let $query := cts:and-query((
  cts:collection-query($collection),
  cts:element-value-query(fn:QName("urn:orders", "status"), $status)
))
let $hits := cts:search(/p:order, $query, ("filtered", "score-zero"))[1 to $size]
return array-node {
  for $hit in $hits
  return object-node {
    "uri": fn:base-uri($hit),
    "id": $hit/p:id/fn:string(.),
    "lines": array-node {
      for $line in $hit/p:line
      return object-node {
        "sku": $line/@sku/fn:string(.),
        "quantity": xs:integer($line/p:quantity)
      }
    }
  }
}
```

Bound/validate `$size` in the caller; select an explicit index or document order
when pagination must be deterministic. An XPath step over several nodes can
normalize document order and eliminate duplicates. Use a `for` loop or simple
map `!` when preserving a query's order/multiplicity. Add an explicit tie-breaker
when sorting on a nonunique value.

The result is a projection, not a document backup. JSON `array-node` preserves
array structure, including an empty array; a flattened XQuery sequence does not.
Choose omission versus JSON null deliberately for absent optional values.
Use `xdmp:quote` for serialization and `xdmp:unquote` when parsing is intended;
`fn:string` is not a serializer for complex nodes or maps.

## Updates and transaction boundaries

Choose the lowest-impact operation: metadata service for metadata, REST PATCH
for a narrow content patch, full document replacement only when needed, or an
existing server module for domain behaviour. Ordinary insertion/replacement
can alter permissions/collections/quality if not preserved; inspect them first.
Temporal and protected documents require their specialised APIs.

Use MarkLogic update functions (`xdmp:node-replace`, `xdmp:node-insert-child`,
`xdmp:node-delete`, `xdmp:document-insert`) rather than assuming another XQuery
processor's update syntax applies. Updating stored nodes differs from building
new in-memory nodes. For a pure transformation, construct a new XML/JSON result;
make persistence explicit. In SJS a module performing updates needs
`declareUpdate()`; it is not a Python transaction flag.

Updates in a statement are pending until it completes. Do not expect a later
expression in the same statement to reread an already committed new version.
Semicolon-separated executable statements can create separate transactions;
prolog declaration semicolons do not mean each declaration is a transaction.
An explicit `xdmp:eval`/invoke can create another transaction and different
database/user/module context: inspect its options and privileges. Avoid nested
updates that wait on locks held by their caller.

For a Python multi-request unit, use the library transaction context and pass
its transaction parameters to **every** participating request. Async dependent
writes remain sequential; `gather` is not atomicity. After ambiguous transport
failure, verify server state before replaying a mutation. Retry is safe only
when the operation's idempotency and transaction semantics allow it.

Catch expected errors narrowly and rethrow others. In XQuery, inspect the
`error:code` in `catch ($error)`; do not replace all failures with `()` or a
successful status. Explicit commits/rollbacks belong to an intentional
transaction design, not boilerplate added to every eval query.

## Modules, security and tests

A library module has `module namespace ...`; importing it requires the matching
URI and installed path. Namespace declaration alone does not import functions.
Read project modules for vocabulary, helpers and domain validation. Reuse
installed FunctX helpers where appropriate; do not assume a namespace prefix
means its library is deployed. Use an installed module invocation for shared
server logic and eval files for ad-hoc code; those are different operations.

Queries run with effective database permissions: an admin sample can expose
more documents than an application user. Missing results can reflect collection,
namespace, database or security scope rather than a broken query. Element-level
security can change visibility inside a document. Imports additionally need
appropriate module read/execute permissions; eval capability is a privilege.
Security API mutations belong to the security database and explicit admin work.

Test empty/single/multiple results, namespace differences, duplicate values,
missing/invalid scalar types, order, fragment correlation and permissions. Use
existing server-side unit-test suites and their setup/teardown in the intended
test database. HTTP mocks test transport/composition; they do not prove native
code, query optimisation or index configuration. Measure equivalent results
before tuning caches, query options or concurrency.
