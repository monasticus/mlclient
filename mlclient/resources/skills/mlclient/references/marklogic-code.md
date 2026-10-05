# Correct and readable MarkLogic code

Apply project style, then existing module conventions, then these defaults.
These are practical conventions adapted from the MarkLogic development knowledge
base; performance claims require measurement on the target data and version.

## XQuery structure and names

- Start standalone code with `xquery version "1.0-ml";`. Declare application
  namespaces explicitly; use expanded QNames when values supply dynamic names.
- Use explicit `fn:` for standard functions and explicit context item `.` in
  path-step calls (`$node/@id/fn:string(.)`). These improve readability; they are
  conventions, not a claim that a bare standard function is always invalid.
- Do not redeclare core prebound prefixes (`fn`, `xs`, `cts`, `xdmp`, `map`).
  Import library namespaces such as admin/search/op from their actual modules;
  a namespace declaration alone does not import their functions. Verify less
  common version-specific prefixes before assuming they are prebound.
- Group imports, namespace declarations and module variables before functions.
  Put public orchestration before helpers so a reader can follow the operation.
  Separate storage, parsing and domain logic when the existing project does.
- Keep function parameters/return types and objective docblocks clear. Explain
  contract, side effects and failure modes; avoid narrating implementation lines.
- Prefer native JSON `object-node`/`array-node` constructors for JSON responses;
  use `map:map` for internal mutable lookup, not merely to build a fixed JSON body.

```xquery
xquery version "1.0-ml";
declare namespace p = "urn:products";
declare variable $collection as xs:string external;
declare variable $start as xs:integer external;
declare variable $size as xs:integer external;

let $query := cts:collection-query($collection)
let $hits := cts:search(/p:product, $query, ("filtered", "score-zero"))
return document {
  object-node {
    "estimated-fragments": xdmp:estimate($hits),
    "items": array-node {
      for $hit in fn:subsequence($hits, $start, $size)
      return object-node {
        "uri": fn:base-uri($hit),
        "name": $hit/p:name/fn:string(.)
      }
    }
  }
}
```

Validate positive/bounded start/size before running this template. Use
`cts:document-order` or a suitable index order for deterministic pagination.
The estimate is deliberately labelled; it is not an exact count of nested nodes.

## Values and sequence semantics

- General comparison `=` compares any pair in sequences. Value comparison `eq`
  requires zero-or-one atomic value on each side. Choose based on cardinality,
  not style. To test membership, `$value = $sequence` is often intentional.
- Effective boolean value of nodes is existence, but a multi-item atomic
  sequence can raise an EBV error. Use `fn:exists`, `fn:empty`, `some` or `every`
  where cardinality is uncertain. Numeric predicates are positional selectors.
- `fn:string(())` returns an empty string; `xs:string(())` returns empty sequence.
  Neither is serialization for a complex JSON/map value. `fn:string` can atomize
  a node; `xs:string` can fail for complex types. Serialize intentionally.
- Use `(candidate, default)[1]` only when sequence cardinality and empty-vs-empty-
  string behavior match the desired default. A present empty string is still
  selected. Use `map:contains` to distinguish missing from a stored empty value.
- Pass supported value sequences directly to cts constructors instead of
  separate searches per value. Use explicit `cts:or-query` otherwise.
- Use simple map `!` for transformations that must preserve hit order. A path
  step over a sequence of nodes can normalize document order and deduplicate.
- Repeated sequence concatenation in a growing accumulator can be quadratic.
  Prefer a sequence comprehension or a JSON array accumulator where mutation is
  warranted; measure large loops.

## Eval, modules and server-side JavaScript

Bind external data. Raw XQuery needs `declare variable $name external;`; raw
server-side JavaScript variables are supplied through the eval contract. Avoid
interpolating user strings into query source. Distinguish query-only code from
updates: even a query-looking fragment can call arbitrary code and mutate data.

For REST extensions, inspect the actual request input node/document before
converting JSON to a map; extract the intended `object-node()` rather than
passing a document or array to `map:get`. Preserve response content-type/status
and documented extension signatures. Register modules/transforms only as an
explicit task, with intended read/execute/update permissions.

MarkLogic server-side JavaScript has MarkLogic APIs and sequence semantics; it
is not Node.js. Avoid Node filesystem/modules/Promises assumptions. Import
server modules with their supported paths and inspect documented xdmp/cts APIs.

Write deployment code against the project's ml-gradle/module conventions.
Uploading a module requires the intended permissions; a successful HTTP upload
does not prove an application user can execute it. Prefer existing templates
and helper libraries (including installed FunctX functions) over reinvention.

## Search correctness and evidence

Read [search](search.md) before choosing estimates, lexicons or subtree paths.
Use `cts:estimate($query)` for an index-only fragment estimate where available;
use `xdmp:estimate(cts:search(...))` when a searchable-path constraint is needed.
For database existence, `xdmp:exists` can avoid unnecessary materialization;
for already-loaded local nodes, `fn:exists` is appropriate. Verify optimization
with `xdmp:plan` and representative timing, not universal percentages.

Check exact function signatures at
`https://docs.marklogic.com/MAJOR.0/FUNCTION`, for example
[cts:search](https://docs.marklogic.com/12.0/cts:search), and use the matching
major-version endpoint contract for REST. Retain errors and boundary behavior in
tests: empty sequence, namespaces, duplicate values, missing indexes and limits.
