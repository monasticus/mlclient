# CTS service: adaptation and API design

Tracking the 2026-09-24 review of `feature/cts-service`.
Implementation and proposals are distinguished below; proposed models and package
moves are not released APIs.

## Work items

| ID | Task | Status |
| --- | --- | --- |
| CTS-1 | Rebase all eight CTS commits onto main after trace-events and env merges | Done: main 3b191c5, rebased tip 89f5649 |
| CTS-2 | Adopt shared HTTP error handling in expression evaluation, sync and async | Done; HTTP and MarkLogic error regression tests pass |
| CTS-3 | Audit and explain native versus Python argument order | Implemented; optional lexicon queries are keyword-only |
| CTS-4 | Add search result XPath after index/range, preserving search order | Implemented; 16 live expression scenarios pass on 10.0-11 |
| CTS-5 | Design lazy bytes-backed CTS results with private score/frequency pairing | Revised 2026-09-25 in CTS-RESULTS-DESIGN.md; not implemented |
| CTS-6 | Design service grouping without tying ownership to HTTP versus custom code | Grouping accepted by user; migration not implemented |
| CTS-7 | Full units/coverage, lint, docs and relevant live checks | Done locally; ML11/12 matrix not rerun here |
| CTS-8 | Public Expression API and removal of private compiler imports from services | Done; import boundary, docs and installed wheel verified |
| CTS-9 | Prefer language-specific XqyExpression/XqyCompilationContext names | Proposed follow-up; code still uses Expression/CompilationContext |
| CTS-10 | Override every result-producing CTS function in sync/async services, including field_values | Deferred until after current commits; catalog-wide audit required |
| CTS-11 | Document builder/eval versus service execution; service variable always cts | Required with result implementation; detailed in results design |

## Workspace preservation

The pre-existing uncommitted edit in `mlclient/services/documents.py` is preserved
in the stash named `user documents.py edit before cts-service rebase`. It was not
folded into this branch. Existing `meta/cts-service-review/` evidence remains
untouched; its older proposals are historical context, not new approvals.

## Adaptation to main

The eight feature commits were replayed, retaining the new environment API,
trace-events service/CLI, and shared response-error handling from main. The eval
import conflict was resolved without restoring the obsolete MarkLogicError
import. Two expression execution paths still constructed that exception directly;
both now use `MLResponseParser.raise_for_status`, like raw XQuery evaluation.
Recognized MarkLogic failures remain MarkLogicError; empty/proxy HTTP failures
remain HTTPStatusError with their request/status/body. Regression tests live in
the owning sync/async eval test modules, with mocks visible inside each test.

CTS has no configuration calls or references to the renamed environment helper.
Its constructor still consumes RestApi; no manager/CLI/environment coupling is
needed. Decimal and other typed-value additions remain in the common parser,
not in a second CTS parser. The existing CI matrix already covers MarkLogic
10/11/12; local results below do not substitute for that matrix.

## CTS-3: argument policy (implemented)

Native names become snake_case. Required native arguments retain relative order
and are positional-or-keyword; optional arguments are keyword-only and retain
relative order. The compiler always restores native argument slots, with `()`
for skipped interior arguments and omitted trailing slots.

| Operation | Native slots | Python contract |
| --- | --- | --- |
| search | expression, query, optional options/quality/forests | expression, query, then keyword-only options; defaults allow `/` and `()` |
| uris | optional start, options, query, quality, forests | all keyword-only, in native order |
| values | range-indexes, optional start/options/query/quality/forests | indexes positional, remainder keyword-only in native order |
| geospatial-co-occurrences | first lexicon, optional children, second lexicon, optional children/options/... | two required lexicons first, all optional arguments keyword-only |

The catalog contract test enumerates every builder and verifies wire argument
positions, including omitted interior slots. The previous query-first exceptions
for uris/values were unnecessary and removed (also from services). No compatibility
aliases are added to this experimental API. Services accept the same calling
conventions; `values` currently calls its required input `references`, while the
native builder uses `range_indexes`. Both mean the same native reference sequence.

The geospatial exception is justified by required/optional grouping, not search
ergonomics. Documented convenience defaults remain: search's `/` expression and
empty query, estimate's empty query, and directory_query's default depth. These
are explicit defaults, not silent positional reordering.

References: [cts:uris](https://docs.marklogic.com/cts:uris),
[cts:values](https://docs.marklogic.com/cts:values),
[cts:search](https://docs.marklogic.com/cts:search),
[cts:geospatial-co-occurrences](https://docs.marklogic.com/cts:geospatial-co-occurrences).

## CTS-4: result XPath (implemented)

Pipeline: **search → index or inclusive range → XPath for each selected hit**.
The emitted simple map `(...) ! (path)` preserves hit order; applying `/path`
to the entire sequence can impose document order. Namespaces and the existing
native preflight guard are shared with the searchable expression. Paths are
external bindings until validation passes; no home-grown XPath parser is added.

Relative paths begin at each hit, absolute paths at its document root. For `/`
searches use `xpath="p:item/p:label"`; for `/p:item` use `xpath="p:label"`.
The native restricted path grammar applies (not arbitrary XQuery or all XPath).
On 10.0-11, `item/label` and `/item/label` pass, whereas `.` and `./item/label`
do not. Empty/non-string arguments fail locally; invalid syntax fails server-side
as MLCLIENT-INVALID-PATH before the main expression runs.

A selected hit may contribute zero or many output items. Range counts hits,
not projected nodes; results keep the existing empty/singleton/list convention.
No URI metadata or new model is implied by this projection feature.

Reference: [cts:valid-extract-path](https://docs.marklogic.com/cts:valid-extract-path).

## CTS-5: typed search results (proposal)

The current proposal is [CTS-RESULTS-DESIGN.md](CTS-RESULTS-DESIGN.md).
It proposes SearchHit/ValueHit directly from existing service operations, with
bytes-backed lazy content, Document-like caches and namespace-aware findall.
There are no twin methods, custom metadata envelopes or as_document operation.
Actual X-URI/X-Path headers are preserved, with '/' for a document node without
X-Path. The later agreed service wrapper explicitly returns score/frequency
partners in the same request; builders/eval remain plain. Public-API ML10 probes
confirmed atom-producing search paths are rejected; search returns nodes.
Empty/singleton/list cardinality is confirmed by the user; preserve it.

## CTS-6: grouping services (accepted design; migration pending)

Group by the user's task and privilege boundary, **not implementation transport**.
Eval is fundamental yet runs caller code; CTS executes generated XQuery; trace
and log-level can use multiple transports. None should move namespaces because
a fallback implementation changes.

| Responsibility | Services | Suggested canonical namespace |
| --- | --- | --- |
| Application content/query/transaction work | Documents, Eval, Transactions, CTS | mlclient.services (keep current imports) |
| Operational diagnosis and observability | Logs, LogLevel, TraceEvents | mlclient.services.diagnostics |

Avoid an extra `core` package: the default namespace already expresses the
application-facing set. Group sync/async variants under the same owner. Logs
belongs with diagnostics because it retrieves server logs through ManageApi;
being useful/frequently used does not make it a content operation. If “core”
instead means shipped/supported, all these services are core in that different
sense; that distinction should not determine Python imports.

Do not add a service registry or duplicate every service onto MLClient. Keep
existing eval/documents accessors and transaction factory. CTS can remain an
explicit `CtsService(ml.rest)` while experimental. Diagnostic construction stays
explicit, making management connections/privileges visible and retaining lazy
auxiliary connections. No `ml.core`/`ml.extra` facade is needed.

The user accepted this grouping; it is not implemented as part of this design turn.
The existing canonical-export policy forbids casually exporting each class from
both namespaces. Decide migration/stability policy before moving anything.

- [x] Accept responsibility grouping, including Logs with diagnostics.
- [ ] Set migration policy for the existing public diagnostic imports.
- [ ] Move diagnostic modules and their canonical exports together if approved.
- [ ] Update CLI/internal imports, docs namespace generation and import-contract tests.
- [ ] Preserve per-module tests/resources and verify an installed wheel outside checkout.

## CTS-8: public expression API (implemented)

`Expression` replaces the abbreviated Expr name, without a compatibility alias
in this experimental API. Canonical import:
`from mlclient.functions.xqy import Expression`. Its defining module is the
public `mlclient.functions.xqy.expressions`, not `_expr`.

Keep it language-specific: compiling XQuery external variables, namespaces,
restricted paths, range/index and simple-map projection is not yet a shared
contract with SJS. A future `mlclient.functions.sjs.Expression` can be independent;
extract a shared protocol only when real callers need one across both languages.

Related boundary changes:

- `CompilationContext` is public because custom Expression.render implementations
  receive it. No private type is necessary for that extension point.
- `Expression.project(path)` owns projection construction. CTS services no longer
  import the private projection node or private builder definition module.
- `namespace_bindings` is a public, documented namespace validation/snapshot helper
  shared by service defaults and compilation.
- Cts/Fn/Xs/Xdmp remain public classes named after the native namespaces. Their
  lowercase instances remain the convenient public entry points.
- Atomic/function-call/range/projection nodes remain private implementation within
  the builder subsystem. AtomicValue is not an extra public model: callers use
  typed xs builders and ordinary Python values.

Public-export and service-import-boundary tests guard this contract. Documentation
and all code references use Expression; historical files under meta are untouched.

## Final verification

- Full unit suite: **2802 passed**, **100% line coverage** (7947 statements).
- Live expression scenarios: **16 passed**, local **MarkLogic 10.0-11**;
  includes sync/async projection ordering, slicing, namespaces and invalid paths.
- Ruff and `git diff --check`: pass; no new lint suppressions.
- `make docs-build`: pass, **223 HTML pages** checked.
- Wheel/sdist build: pass. Wheel installed outside the checkout; public imports,
  projection compilation, absence of the old `_expr` module and CLI help verified.
- `origin/main` is an ancestor of the rebased branch. Follow-up changes remain
  uncommitted; no push performed. The user edit remains in its named stash.
