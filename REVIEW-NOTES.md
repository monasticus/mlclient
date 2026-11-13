# Review notes - feature/v1-17-documents-exists

## Items

- D3. HEAD `/v1/documents` as `documents.exists(uri)`

## Original plan

- Decision: do - `exists` via HEAD, one URI. No search / cts involvement, no multi-URI helper.
  1. Call: `DocumentsHeadCall(uri, database=None, txid=None)` modelled on `TimestampHeadCall`; one `uri` (the
     server rejects several with 400); no `category`, `format`, `Range`, `timestamp` (undocumented for HEAD).
  2. API: `ml.rest.documents.head(uri, *, database, txid, timeout)` returning the raw response, sync and async.
  3. Service: `ml.documents.exists(uri, *, database=UNSET, txid=UNSET, timeout=UNSET) -> bool`, `database` /
     `txid` resolved through `ServiceScope` like `read`. 200 -> `True`, 404 -> `False`, any other status raises
     (`HTTPStatusError` - HEAD carries no error body). Sync and async.
  4. Docs: `exists` docstring and a short entry in the documents guide.
  5. Tests: unit (Call URL and params; service 200 / 404 / 401); integration in the CI matrix (existing, missing,
     inside a transaction with and without `txid`).

## What was added or changed around it

- `exists` checks for 404 first and then hands the response to `MLResponseParser.raise_for_status`, the same
  check `read` / `write` / `delete` use. For a HEAD response, which has no body, that check always raises
  `httpx.HTTPStatusError`. A 2xx other than 200 counts as `True`, but MarkLogic only returns 200 for HEAD.
- `DocumentsHeadCall` does not reject a list of URIs on the client side. It is typed `uri: str`, and MarkLogic
  answers 400 to several URIs. This matches how the other Calls handle server-side constraints that no probe
  required them to enforce.
- Documents guide: the intro now says that `read` / `write` / `delete` accept many URIs and `exists` takes one.
  The "Within a transaction" section lists `exists` too.

## Report

- **Behaviour / public API**
  - New `mlclient.calls.DocumentsHeadCall(uri, database=None, txid=None)` sends `HEAD /v1/documents`.
  - New `ml.rest.documents.head(uri, *, database=None, txid=None, timeout=UNSET)`, sync and async, returns the
    raw response.
  - New `ml.documents.exists(uri, *, database=UNSET, txid=UNSET, timeout=UNSET) -> bool`, sync and async. It
    uses the service scope (`ml.documents(txid=...)`) the same way `read` does.
- **Files**
  - `mlclient/calls/documents.py`
  - `mlclient/calls/__init__.py`
  - `mlclient/api/documents.py`
  - `mlclient/services/documents.py`
  - `docs/guides/documents.md` (new section "Check that a document exists")
- **Tests**
  - Unit:
    - `tests/unit/mlclient/calls/test_documents_head_call.py`: endpoint, method, params, headers, body and a
      fully parametrized call.
    - API `test_head_documents` in `test_rest_api.py` and `test_async_rest_api.py`: params, raw headers,
      timeout.
    - Service tests in `test_documents.py` and `test_async_documents.py`: 200 gives True, 404 gives False, 401
      raises `HTTPStatusError`; request kwargs and timeout are passed through; the service scope is inherited;
      `None` clears the scope.
    - `test_public_api.py` has the new export.
    - The mocked headers come from a real MarkLogic 12.1 HEAD response.
  - Integration: two tests added to `tests/integration/mlclient/services/test_documents_service.py`. One
    covers a missing and then an existing document. The other covers a document written in an open transaction:
    `True` with `txid`, `False` without it, then rollback. These were not run locally because they need the
    project's docker MarkLogic. CI runs them on 10.0-11.1, 11.3.7 and 12.1.
  - Full unit suite: 10443 passed, 3 failed. The 3 failures are the known order- and load-dependent
    `test_env_compare_command` / `test_env_show_command` disclosure tests. They pass when run on their own and
    also fail on the base commit. The new code in `api/documents.py` and `services/documents.py` is fully
    covered. Ruff check and format are clean. `mkdocs build --strict` and `scripts/check_docs.py` pass.
- **Verified against local MarkLogic 12.1** (environment `local`, URIs `/mlclient-v1-17/exists.json` and
  `/mlclient-v1-17/exists-txn.json`, both removed or rolled back afterwards):
  - missing gives False; after writing, True; after deleting, False
  - `rest.documents.head` returns 200 with an empty body and `vnd.marklogic.document-format: json`
  - document written in an open transaction: True with `txid`, True through `ml.documents(txid=...)`, False
    without `txid`, False after rollback
  - an unknown `database` makes the server answer 400, which raises `HTTPStatusError`
  - async client: same results for missing, existing and deleted

## Open points for the reviewer

- None.
