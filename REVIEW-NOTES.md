# Review notes - feature/v1-15-documents-params

## Items

- D1. `DocumentsService.read`/`write` do not pass parameters the API supports
- D5. Minor `/v1/documents` validation mismatches

## Original plan

### D1

  - Decision: do, as planned below (approved 2026-11-13).
    1. `ServiceScope` unchanged. `timestamp`, `transform`, `transform_params` are per-call parameters (like
       `category`), not scope - unlike `SearchScope`, because `ServiceScope` is shared with eval/invoke, which
       accept neither.
    2. `read` / `read_stream` (sync `services/documents.py:170,224`, async `:524,580`): keyword-only
       `transform: str | None = None`, `transform_params: dict | None = None`, `timestamp: str | None = None`,
       passed to `self._rest.documents.get(...)`. In `read_stream` (and the batched `read`) the same `timestamp`
       goes to every batch, so the whole read sees one snapshot.
    3. `write` (sync `:115`, async `:469`): `transform`, `transform_params`, `system_time: str | None = None`,
       passed to `self._rest.documents.post(...)`.
    4. Client-side validation before any request (`WrongParametersError`):
       - `timestamp` together with an effective `txid` (argument or scope) - MarkLogic answers
         `XDMP-UPDATETIMESTAMP` as a 500 `INTERNAL ERROR`;
       - `system_time` without `temporal_collection` - MarkLogic silently ignores it;
       - `transform_params` without `transform`.
    5. No automatic snapshot in `read_stream` (taking the first batch's `ML-Effective-Timestamp` for the rest):
       a long stream could then fail with `XDMP-OLDSTAMP` after a merge where it works today. A snapshot is opt-in
       by passing `timestamp`.
    6. Docs: a section in the documents guide on transforms (read and write, `trans:` params, content parts only)
       and snapshot reads, with the example search -> `documents.read(uris, timestamp=report.effective_timestamp)`;
       note `XDMP-OLDSTAMP` (the server must retain that version - merge timestamp) and the `system_time`
       privilege.
    7. Tests:
       - unit: each parameter reaches the API call (sync and async, every batch of `read_stream`); the three
         validation errors;
       - integration, in the existing CI matrix (`10.0-11.1-ubi-2.2.4`, `11.3.7-ubi-2.3.0`, 12.1): install a test
         transform, read (single and multi-document) and write with it and its `trans:` parameter, read several
         documents at an earlier `ML-Effective-Timestamp` after an update and get the old content - this is the
         check that the parameters behave the same on every supported version.
    - Changelog: new parameters on `documents.read`, `read_stream`, `write`.

### D5

  - Decision: do both (breaking for `binary` / `text`, accepted before 1.0).
    1. `DocumentsGetCall._SUPPORTED_FORMATS` (`calls/documents.py:48`) becomes `["json", "xml"]`; any other value
       raises `WrongParametersError("The format applies to metadata only; supported formats are: json, xml")`. The
       separate metadata-format check then has nothing left to do and goes; the Accept-header logic keeps using
       `data_format` as today.
    2. Category check: normalise `category` to a list once (`None` -> `["content"]`, a string -> `[string]`) and use
       "any category other than content" instead of `category != "content"`, so `["content"]` behaves like
       `"content"`.
    3. Check `DocumentsPostCall` / `DocumentsDeleteCall` for the same string-vs-list comparison and fix it the
       same way where present.
    4. Tests: the five cases of the table above with the new results (`["content"]` + `json` OK; `text` /
       `binary` rejected for any category; `metadata` + `json` OK).
    - Changelog: `data_format` of documents calls accepts only `json` / `xml`.

## What was added or changed around it

- **Parameter order.** The new keyword-only parameters sit next to the related ones: `read` / `read_stream`
  take `category, transform, transform_params, timestamp, database, txid, timeout`; `write` takes
  `transform, transform_params, database, temporal_collection, system_time, txid, timeout`.
- **Validation messages** (all `WrongParametersError`, raised before any request):
  `timestamp cannot be combined with txid`, `system_time requires temporal_collection`,
  `transform_params require transform`. The txid check uses the effective txid, so a scoped txid counts and
  `txid=None` clears it (tested). In `read_stream`, a generator, the error is raised when iteration starts,
  like the existing category validation; `read` raises it at once.
- **D5 empty category.** `category=None`, `""` and `[]` are all treated as content (the server default), so an
  empty list keeps its old behaviour (no metadata Accept header).
- **D5 point 3.** `DocumentsPostCall` has no `category`; `DocumentsDeleteCall` already turns `category` into a
  list for validation and does no string comparison, so neither needed a change.
- **New finding, documented: `timestamp` + `database`.** On local MarkLogic 12.1, a GET `/v1/documents` with
  `timestamp` **and** a `database` other than the REST server's default database ignores the timestamp without
  any message. It returns the latest content, and even `timestamp=1` gives 200 instead of `XDMP-OLDSTAMP`.
  Without `database`, or with `database=<the default database>`, the timestamp works (old content returned,
  `timestamp=1` -> 500 `XDMP-OLDSTAMP`). The guide and docstrings say so. There is no client-side check,
  because the client does not know the server's default database. The integration test uses the default
  database.
- **Changelog.** The project has no changelog file; release notes are generated from PR labels
  (`.github/release.yml`). The PR should carry `breaking` (D5: `data_format` of `DocumentsGetCall` accepts only
  `json` / `xml`) and `feature` (D1: new `transform`, `transform_params`, `timestamp` on `documents.read` /
  `read_stream`, and `transform`, `transform_params`, `system_time` on `documents.write`).

## Report

**Behaviour / public API**
- `ml.documents.read`, `read_stream` (sync and async): new `transform`, `transform_params`, `timestamp`,
  passed to every batch request. With `timestamp`, the whole read uses one snapshot. The service does not take
  a snapshot by itself.
- `ml.documents.write` (sync and async): new `transform`, `transform_params`, `system_time`.
- The three client-side validation errors above. `ServiceScope` is unchanged.
- `DocumentsGetCall`: `data_format` accepts only `json` / `xml`; anything else raises
  `The format applies to metadata only; supported formats are: json, xml`. The separate metadata-format check
  is gone. `category` is turned into a list once, so `["content"]` behaves like `"content"` (no metadata Accept
  header). `["collections"]` behaves like `"collections"`.

**Docs** - `docs/guides/documents.md`: new sections "Transforms" and "Point-in-time reads" (search report ->
`documents.read(uris, timestamp=report.effective_timestamp)`, `XDMP-OLDSTAMP` / merge timestamp, no txid, the
`database` caveat), and "Set the system time" under temporal documents (needs `temporal_collection` and the
`temporal-statement-set-system-time` privilege). `mkdocs build --strict` and `scripts/check_docs.py` pass.

**Files**
- `mlclient/calls/documents.py`, `mlclient/services/documents.py`, `docs/guides/documents.md`
- `tests/unit/mlclient/calls/test_documents_get_call.py`, `tests/unit/mlclient/services/test_documents.py`,
  `tests/unit/mlclient/services/test_async_documents.py`
- `tests/integration/mlclient/services/test_documents_service.py`,
  `tests/resources/integration/mlclient/services/test-documents-service/tag-transform.xqy`

**Tests**
- Unit: parameters reach the request (strict params) for read, write, and every batch of a 2000-URI
  `read_stream`; the three validation errors (txid as an argument and from the scope, plus clearing a scoped
  txid); D5 format/category matrix (`binary`/`text`/`html` rejected for every category form; `json`/`xml`
  accepted for every category form; Accept header for `["content"]` and `["collections"]`). Sync and async.
  Full suite: **10470 passed**. Ruff check and format are clean for the touched files.
- Integration (written, **not run locally** - CI matrix 10.0-11.1, 11.3.7, 12.1): a module-scoped test
  transform is installed and removed. The tests cover a single-document read with transform and `trans:`
  param, a multi-document read with transform, a write with transform (the stored content is transformed),
  and a multi-document read at an earlier `ML-Effective-Timestamp` after an update (old content) compared
  with a plain read (new content).

**Verified against local MarkLogic 12.1** (with this branch's code; temporary transform `mlclient-v1-15-tag`
and documents `/mlclient-v1-15/*` were created and then removed). Transform on single and multi-document reads:
both work. Write with transform: the transformed content is stored. Metadata-only read with transform:
metadata returned. The three validation errors: all raised. Point-in-time reads work on the default database
and are ignored with a non-default `database` (see above).

## Follow-up code review (2026-11-13)

### Preserve transform parameters with false, zero and empty values

Both document Calls dropped falsy transform parameters through ApiCall.add_param. Reuse the existing query_params helper in GET and POST, omitting only None, shared by sync/async services and raw APIs. Two regression tests failed before the fix; affected suites: 254 passed. Full unit suite: 10472 passed, 100% coverage. Live MarkLogic 10.0-11 and 12.1.0: read with False/0/empty transform values, write transform False, and old/current snapshot reads passed, with uniquely named fixtures removed in finally.

## Open points for the reviewer

- `timestamp` with a non-default `database` is ignored by MarkLogic 12.1 without any message. It is documented,
  not checked. Should the docs ask users to scope to the server's default database, or is a warning in the
  guide enough? Not checked on 10/11.
- D5 is breaking for `DocumentsGetCall(data_format="binary" | "text")` (accepted before 1.0, as decided).
