# Review notes - feature/v1-19-rest-extensions

## Items

- L1. `/v1/resources/{name}` (REST extensions) - the decided invocation part only.

## Original plan

The `Decision:` of L1, copied verbatim:

> - Decision: do in 1.0 - the invocation part (Calls, `ml.rest.resources.get|post|put|delete`, service
>   `ml.resources.get|post|put|delete` with params, bodies, scope, parsing) as designed above, approved 2026-11-13,
>   on the "Endpoint capabilities" branch.
>   - **? Open: management** (`/v1/config/resources` Calls, `ml.rest.resources.config`, `ml.resources.install`,
>     `list`, `source`, `remove`) - the author is not sure yet whether mlclient should cover it; decide before the
>     branch starts.

"As designed above" refers to points 1-3, 5 and 6 of the item's proposed design (invocation part):
Calls `ResourceGetCall` / `ResourcePostCall` / `ResourcePutCall` / `ResourceDeleteCall` with the `rs:` prefix
added by a `query_params`-style helper; `ml.rest.resources.get|post|put|delete` (raw, sync and async); the
`ml.resources` service with `ServiceScope` and the scoped copy; params without prefix, list values repeated, keys
already starting with `rs:` unchanged, bool / number serialisation; bodies dict / list -> JSON, str / bytes with an
explicit `content_type`, a `Document` with its own content type, a list of `Document`s -> `multipart/mixed`;
parsed results like `ml.eval`; a guide page "REST extensions"; unit and integration tests.

## What was added or changed around it

- Out of scope and not implemented: the management part (`/v1/config/resources`, `install` / `list` / `source` /
  `remove`, `ml.rest.resources.config`) - still undecided - and L3. The integration tests install and remove their
  test extensions with plain `ml.http.put` / `ml.http.delete` to `/v1/config/resources/{name}` in a fixture.
- The `rs:` serialisation lives in the Call layer (`extension_params` in `mlclient/calls/_utils.py`, next to
  `query_params`), not only in the service, so `ml.rest.resources` and custom Call users get the same prefixing,
  list repetition and `true` / `false` booleans. The service passes `params` through.
- Body kinds are split by layer: the Calls accept `dict` / `list` (JSON string, `application/json` unless a
  `content_type` is given) and `str` / `bytes` (`content_type` required, otherwise `WrongParametersError` before
  any request; other types are rejected too). `Document` and lists of `Document`s are converted by the service
  (`mlclient/services/resources.py`), because Calls do not depend on models. A `Document`'s content type comes
  from its URI extension (`Mimetypes`), or from its document type when the URI is missing or unknown
  (json / xml / text/plain / application/octet-stream). Multipart parts carry only `Content-Type` - MarkLogic 12.1
  accepted that (probe below).
- Two small guards beyond the design: a `content_type` passed together with `Document`(s) is rejected (a Document
  carries its own type), and a `MetadataDocument` (no content) is rejected with a clear message.
- `ResourcesService` / `AsyncResourcesService` subclass the existing `ExecutionService` (scope, scoped copy via
  `__call__`, `raise_for_status` + `MLResponseParser.parse`) instead of copying that code; the base docstring now
  names resource extensions too.
- Signatures: service `get(name, params=None)`, `post|put(name, body=None, params=None, *, content_type=None)`,
  `delete(name, params=None)`, all with keyword-only `database`, `txid` (UNSET inherits, None clears) and `timeout`.
  The raw API takes everything except `name` keyword-only and adds `accept` (Accept header). The service has no
  `accept` option (not in the design).
- The extension name is percent-encoded as a path segment (as `/v1/values/{name}` does).

## Report

What changed:

- Calls: `mlclient/calls/resources.py` (`ResourceGetCall`, `ResourcePostCall`, `ResourcePutCall`,
  `ResourceDeleteCall`, exported from `mlclient.calls`); helper `extension_params` in `mlclient/calls/_utils.py`.
- API: `mlclient/api/resources.py` (`ResourcesApi`, `AsyncResourcesApi`, exported from `mlclient.api`), wired as
  `ml.rest.resources` in `RestApi` / `AsyncRestApi`.
- Service: `mlclient/services/resources.py` (`ResourcesService`, `AsyncResourcesService`, exported from
  `mlclient.services`), exposed as `ml.resources` on `MLClient` / `AsyncMLClient`.
- Docs: new guide `docs/guides/rest-extensions.md` (calling only: params table, body kinds, multipart in/out,
  scope and transactions, errors, the execution-user difference 12.0.2 vs 12.0.1 / 12.1.0, raw API) in the
  mkdocs nav; `docs/advanced/services.md`, `docs/guides/clients.md` and `README.md` list the new service. The API
  reference is generated from `__all__`.

Tests:

- Unit: `tests/unit/mlclient/calls/test_resource_{get,post,put,delete}_call.py`, `extension_params` cases in
  `test_call_utils.py`, wire-level API tests in `tests/unit/mlclient/api/test_rest_api.py` and
  `test_async_rest_api.py` (repeated params, Accept, JSON / XML bodies, error passthrough, rejection before any
  request), service suites `tests/unit/mlclient/services/test_resources.py` and `test_async_resources.py`
  (37 each: prefixing, repetition, serialisation, every body kind, Document content types, multipart request
  parts, JSON / XML / multipart / empty results, scope inherit / override / clear, MarkLogicError with the full
  message, HTTPStatusError), public exports in `test_public_api.py`. Mocked responses are based on real
  MarkLogic 12.1 responses captured from the probes below.
- Full unit suite: 10576 passed, line coverage 100.00%. `ruff check .` clean; `ruff format --check` clean for all
  touched files (two untouched CLI test files were already unformatted on the base).
- Docs: `mkdocs build --strict` and `scripts/check_docs.py` pass.
- Integration: `tests/integration/mlclient/services/test_resources_service.py` (11 tests) installs an XQuery and a
  JavaScript echo extension (`tests/resources/integration/mlclient/services/test-resources-service/`) with plain
  HTTP and removes them in `finally`: GET with single, repeated, pre-prefixed and boolean / number params, the
  JavaScript extension, POST with a JSON body, POST with Documents as multipart, multipart response as a list, PUT
  with a str body, DELETE, scoped database, missing extension -> `MarkLogicError`, and the raw API vs an
  unprefixed parameter (400 `REST-UNSUPPORTEDPARAM`). Run locally against MarkLogic 12.1.0 (port 8000) with the
  extension names renamed to `mlclient-v1-19-echo` / `mlclient-v1-19-echo-sjs`: 11 passed. Not run on the CI
  matrix (10.0-11.1, 11.3.7, 12.1) - CI will run them.

Verification against local MarkLogic 12.1.0 (App-Services, 8000), extension `mlclient-v1-19-echo` installed via
`PUT /v1/config/resources` and removed afterwards (`GET /v1/config/resources` lists nothing at the end):

| Request | Result |
|---|---|
| GET `rs:a=x&rs:a=y&rs:flag=true&rs:n=3` | 200 JSON, extension receives `a` as a sequence, `flag` / `n` as strings |
| GET `a=x` (no prefix) | 400 `REST-UNSUPPORTEDPARAM` |
| PUT / POST JSON, XML, text, octet-stream bodies | 200, input types as sent |
| POST multipart/mixed, 3 parts with only Content-Type | 200, extension receives 3 documents |
| POST, extension returns 3 documents | 200 multipart/mixed, parsed to `[dict, ElementTree, str]` |
| unknown extension | 500 `INTERNAL ERROR` / `RESTAPI-INVALIDREQ` |
| JavaScript extension GET | 200 JSON, repeated params as an array |
| `ml.resources` sync and async (`AsyncMLClient`) via the worktree code | results as expected, scoped `database` honoured |

## Follow-up code review (2026-11-13)

### Support inherited Document implementations

The new Document body path revealed that Document.__subclasshook__ only inspected the immediate class dictionary and was inherited by concrete document types, confusing document identities. Honor inherited concrete properties in the Document check and use normal subclass checks for concrete types. Metadata-only body validation uses isinstance. Regression coverage includes custom JSONDocument bodies and MetadataDocument subclasses, sync and async, plus concrete document identity. Affected model/service suites: 331 passed. Existing 11 resource integration tests passed on both local MarkLogic 10.0-11 and 12.1.0; test extensions were removed afterwards. Full unit suite after the repair: 10581 passed, line coverage 100.00%. Ruff and the strict docs build plus check_docs.py passed (490 HTML pages validated).

## Open points for the reviewer

- Management (`/v1/config/resources`) remains undecided and is not on this branch. The guide says the extension
  must already be installed and does not show how to install one.
- The integration test for a missing extension asserts the exact 12.1 message (500 `INTERNAL ERROR` wrapping
  `RESTAPI-INVALIDREQ`). The checklist research saw the same on 12.1; MarkLogic 10 / 11 were not probed and may
  word or code it differently - check the CI matrix run.
- The service has no `accept` option (the raw API has one). Add it if extensions answering in several formats
  matter for `ml.resources`.
- The vault note says undeclared GET parameters are rejected; on 12.1 an extension installed without parameter
  declarations accepted any `rs:` parameter. The guide does not mention declarations (management is out of scope).
