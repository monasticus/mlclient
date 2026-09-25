# CTS service: implementation tracker

Tracking the 2026-09-24/25 review of `feature/cts-service`. The expression/CTS
APIs remain experimental. Latest result contract: [CTS-RESULTS-DESIGN.md](CTS-RESULTS-DESIGN.md).

## Work items

| ID | Task | Status |
| --- | --- | --- |
| CTS-1 | Rebase eight CTS commits onto main after trace-events and env merges | Done: main 3b191c5, rebased tip 89f5649 |
| CTS-2 | Adopt shared HTTP error handling in sync/async evaluation | Done; recognized MarkLogic and generic HTTP failures covered |
| CTS-3 | Align native/Python argument order | Done; optional native slots are keyword-only; values uses range_indexes in both layers |
| CTS-4 | Project search XPath after range/index, preserving hit order | Done; original score retained for every projected node |
| CTS-5 | Result models and score/frequency transport | Done; parsed content from MLResponseParser, original bytes retained, no model parser |
| CTS-6 | Group diagnostics by responsibility | Done; canonical mlclient.services.diagnostics imports and per-module tests/resources |
| CTS-7 | Full verification after implementation | Done locally: 2962 units/100%, 19 ML10 scenarios, Ruff, docs and installed wheel; ML11/12 not rerun |
| CTS-8 | Public expression/compiler extension API | Done; services do not import private expression implementations |
| CTS-9 | XqyExpression/XqyCompilationContext naming | Done across exports, code, tests and docs; no speculative SJS superclass |
| CTS-10 | Execute all result-producing CTS operations | Done; 100 sync/async operations and 91 composable constructors, including field_values |
| CTS-11 | Document builder/eval versus service; service variable always cts | Done in Python search/services guides |

## Workspace and commits

- First requested commit: `664fc26`, adapting the rebased branch to main and
  recording the initial public-expression/result contracts.
- The pre-existing documents.py edit remains recoverable in the stash named
  `user documents.py edit before cts-service rebase`; it was not folded into CTS.
- Existing untracked `meta/` research remains untouched and is not committed.
- No push is authorized for this continuation; commits remain local.

## Argument and composition policy

Required native parameters preserve their relative order and are positional or
keyword. Optional native parameters are keyword-only, retaining native order.
The compiler restores empty interior native slots and omits unused trailing ones.
Thus uris accepts query= consistently without inventing a query-first signature.

Native geospatial calls that interleave required/optional arguments group required
parameters first in Python. This follows the required/optional rule; it is not
an arbitrary search convenience. Search additionally allows expression=None
(meaning '/') and query=None (empty native query); estimate permits query=None.

Native `Cts.method(...)` always builds an expression, including nested searches,
lexicons and aggregates. `cts = CtsService(...)` executes result operations.
Query/reference/order/geometry/entity-dictionary constructors remain expressions
on the service as well. Tests explicitly classify all 191 supported functions;
new catalog entries cannot silently become inherited non-executing lookups.

## Result contract: latest user decision

Models receive already parsed content, not headers or bytes to parse later.
`MLResponseParser.parse_part` is the public shared per-part parser, reused by
generic eval and the service. SearchHit/ValueHit retain original MultipartPart
bytes without reserialization. Their common base only stores content/snapshots
and offers local XML findall plus text-snapshot decoding.

Empty/singleton/list cardinality is preserved, including index=1. Score/frequency
are extracted in the same eval request and paired internally; native expressions
do not acquire extra measure parts. JSON scalar/text, XML, TXT and binary results
use the existing parser. Missing source path becomes '/' independently of type.
Mutating parsed content does not alter original bytes; no invalidate API or
duplicate parser exists. See the result design for wire evidence and edge cases.

## Public imports and service ownership

- `mlclient.functions.xqy`: XqyExpression and XqyCompilationContext are public;
  their owner is the public expressions module. Cts/Fn/Xs/Xdmp and lowercase
  builder instances remain public. Private expression nodes stay private.
- `mlclient.services`: application content, eval, transactions and CTS.
- `mlclient.services.diagnostics`: LogsService/AsyncLogsService, LogLevelService,
  TraceEvents and TraceEventsService. No duplicate legacy exports.

Grouping follows operational responsibility, not whether implementation invokes
REST or custom XQuery. There is no extra core namespace, registry or client facade.
Moves include CLI imports, docs generation, public import checks and fixtures.
The unrelated omnibus test_xqy_services module has been removed: tests now live
with eval or CTS, with request mocks visible in each test.

## Verification

- Earlier baseline in 664fc26: 2802 unit tests, 100% line coverage, 16 ML10 scenarios.
- Final full run: 2962 unit tests, 100% line coverage (8666 statements).
- Latest live run after the parsed-model revision: 19 scenarios pass on ML10.0-11,
  including mixed content, binary write/read/cleanup, positive score projection,
  field values, aggregates and literal/expression-valued map-option rejection.
- Strict documentation build: 227 HTML pages validated, including links/exports.
- Wheel/sdist build and outside-checkout imports/live CTS: pass. The wheel check
  found a pre-existing broken `python -m mlclient` import; fixed with a regression
  test. Both installed `ml --help` and `python -m mlclient --help` now pass.
- ML11/12 environments are not running locally; no new cross-version pass is claimed.
- Ruff and git diff --check pass. No new lint suppression is needed: the approved
  constructor exception was removed once parsed-content dataclasses replaced it.
- Changes are committed locally at handoff; no push performed.
