# Review notes - feature/v1-03-errors-and-parsing

## Items

- A6. `MLResponseParser.parse_with_headers` returns a tuple or a list depending on the response (docs only)
- A7. Common exception base and fields on `MarkLogicError` (A7a fields, A7b `MLClientError`)
- C4. Error parser crashes on its own (`parse()` / `parse_with_headers()` raise for error responses)
- C5. MarkLogic error message lost on paths that bypass `MLResponseParser.raise_for_status`

## Original plan

### A6

  - Decision: no behaviour change in either function - the collapsing is intended. Document it only, in the
    docstrings of `parse()` and `parse_with_headers()` (and the parser section of `docs/guides/clients.md`):
    the list shape belongs to multipart responses, but a multipart with a single part is unwrapped to its item,
    so calls where the user expects one answer (an eval returning one value, a documents read of one document)
    stay simple; callers iterating over a multipart result whose item count varies must handle one item and `[]`.

### A7

  - Decision: do both parts.
    - A7a - `MarkLogicError` keeps the error values as attributes `status_code`, `status`, `message_code`,
      `message` (all `None` when the error came as a raw string); `str(e)` stays exactly as today. Lets callers
      write `if e.message_code == "RESTAPI-NODOCUMENT"` instead of matching `str(e)`.
    - A7b - add `class MLClientError(Exception)` and make all 15 library exceptions in `mlclient/exceptions.py`
      subclass it, so `except MLClientError` catches everything mlclient raises; existing `except ConfigError`
      etc. keep working.
    - Not in scope: `ConfigError` also subclassing `ValueError`; wrapping httpx transport errors (document only
      that their base is `httpx.HTTPError`).

### C4

  - Decision: do - `parse()` raises for an error response (breaking, accepted before 1.0).
    - `MLResponseParser.parse()` and `parse_with_headers()` (`responses.py:117,151`) start with
      `cls.raise_for_status(response)`: a MarkLogic-described error raises `MarkLogicError` (with the A7a fields),
      anything else (empty body, HTML/XML from a proxy, malformed payload) raises httpx's `HTTPStatusError` with the
      original response. A success response parses as today (A6 collapsing unchanged).
    - Remove the error branch of `_parse` / `_parse_text` / `_parse_bytes` that returned the error as a value; keep
      `_parse_xml_error` / `_parse_html_error` only as far as `raise_for_status` still needs them, made total
      (`headers.get(..., "")`, `findtext`) so they never raise themselves.
    - Services already call `raise_for_status()` before `parse()`; the duplicate call can go, behaviour unchanged.
    - Update the docstrings ("Raises" sections) and `docs/guides/clients.md` (parse a response): `ml.parser.parse`
      raises on a non-success response instead of returning the error.
    - Tests: the six response shapes from the table above - each raises (`MarkLogicError` for the MarkLogic JSON
      and XML errors, `HTTPStatusError` for the rest), none returns `''` or a dict; success parsing unchanged.
    - Changelog: `parse()` / `parse_with_headers()` no longer return MarkLogic errors as values.

### C5

  - Decision: do - route all three through `MLResponseParser.raise_for_status(response)`.
    - `_cluster_health_from_status` (`_client.py:1388`) and `MarkLogicCloudAuth._access_token` (`auth.py:320`):
      replace `response.raise_for_status()`; a MarkLogic-described error raises `MarkLogicError` (A7a fields),
      anything else `HTTPStatusError` as today.
    - `_restart.py:574` (`_raise_unexpected_timestamp_status`): no `AssertionError`; pass the response and call
      `MLResponseParser.raise_for_status(response)`, keeping the context (host, "while waiting for restart") in
      the message - e.g. a note added to the exception or chained from a short `MLClientError` (A7b) - so the
      caller sees both the server's answer and what mlclient was doing.
    - Update the "Raises" docstrings (`cluster_healthcheck`, `restart` / `wait_for_restart_completion`, Cloud
      auth). Tests: a JSON `errorResponse` body (e.g. 403 `SEC-PRIV`) on each path gives `MarkLogicError` with
      `message_code`; an HTML 401 still gives `HTTPStatusError`.

## What was added or changed around it

- `MarkLogicError.status_code` is converted to `int`. The Management API reports `statusCode` as a string
  (`"400"`, checked on local MarkLogic 12.1 with `GET /manage/v2?view=nonsense`), so without the conversion
  `e.status_code == 404` would depend on the API that answered. `str(e)` is unchanged (it prints the value as
  received). A non-numeric or missing status code gives `None`.
- `MLClientError` is the 15th class in `mlclient/exceptions.py` (14 existing + the base). The CLI-internal
  `UnsuccessfulAnswerError` (`cli/commands/_multi_env_common.py`) is not a library exception and was left as is.
  The module docstring list also gained the two exceptions it was missing (`InvalidLogTypeError`,
  `EnvironmentFileExistsError`).
- C4 refactor of `responses.py`: `_parse_text` / `_parse_bytes` were copies of `_parse` differing only in the
  output type; they are merged into one `_parse(response, output_type, with_headers)` now that the error branch is
  gone. Error extraction moved to `_parse_error` (dispatch by content type), `_parse_json_error`,
  `_parse_xml_error` (uses `findtext`, total), `_parse_html_error` (returns `None` for unparsable bodies) and
  `_described_error` (the existing "has a messageCode or message" check). None of them raises. Success parsing now
  also tolerates a missing Content-Type (`headers.get(..., "")`).
- An XML error without `message-code` but with a `message` now raises `MarkLogicError` (fields filled,
  `message_code=None`) instead of `HTTPStatusError`: it is a MarkLogic-described error, and the decision groups
  "the MarkLogic JSON and XML errors" under `MarkLogicError`. A non-MarkLogic XML body (502 from a proxy) still
  gives `HTTPStatusError`.
- Two internal callers relied on `parse()` returning an error as a value and had to change (behaviour kept):
  - `services/diagnostics/log_level.py` `_error_body` now returns a `MarkLogicError` (taken from
    `raise_for_status`, or built from the raw text) instead of a dict/str; `_is_privilege_error` reads
    `error.message_code`. Messages are identical.
  - `services/transactions.py` `_txid_or_raise` calls `raise_for_status`; it used to index
    `parse(resp)["errorResponse"]`, which crashed with `TypeError` for a non-JSON error (e.g. an HTML 401).
    A non-303 success answer (cannot normally happen) raises
    `MarkLogicError("Expected 303 See Other when opening a transaction, got N.")`.
- Duplicate `raise_for_status()` calls directly before `parse()` / `parse_with_headers()` were removed
  (`documents.py` x2, `transactions.py` x2, `_execution.py`, `search.py` x1). Where a `if not response.content:
  return []` check sits between them (`search.py`, `cts.py` x3) `raise_for_status()` stays, otherwise an empty
  error body would return `[]`.
- C5 restart: `_raise_unexpected_timestamp_status(host, response)` raises the server's answer
  (`MarkLogicError` or `HTTPStatusError`) chained (`raise ... from`) from
  `MLClientError("While waiting for MarkLogic host [h] to restart, /admin/v1/timestamp answered N instead of
  200 OK.")`. Python 3.10 is supported, so `add_note` was not an option; chaining keeps the exception type of the
  server's answer (so `except MarkLogicError` works) while the traceback shows what mlclient was doing. A
  non-retryable success status other than 200 (e.g. 204) raises that `MLClientError` itself.
- "Raises" docstrings added to the public `wait_for_restart` (sync and async), `cluster_healthcheck`, the opening
  of transactions and `MarkLogicCloudAuth._access_token`.
- Docs: `docs/guides/clients.md` "Parse a response" gained the result-shape table (A6), the raising behaviour with
  an example using `message_code` (C4, A7a), and a short "Errors" section (`MLClientError`, httpx errors based on
  `httpx.HTTPError`). `docs/advanced/health-and-administration.md` documents the errors of the Manage fallback
  and of `wait_for_restart`.
- Integration test added: `tests/integration/mlclient/clients/test_api_client.py::
  test_parsing_an_error_response_raises_marklogic_error` (parse / parse_with_headers of a missing document).
- Changelog: the repo has no changelog file; release notes come from PR labels (`.github/release.yml`). The PR
  should carry the breaking-change label with: "`MLResponseParser.parse()` / `parse_with_headers()` no longer
  return MarkLogic errors as values - they raise `MarkLogicError` or `httpx.HTTPStatusError`. New
  `MLClientError` base; `MarkLogicError` exposes `status_code`, `status`, `message_code`, `message`.
  `wait_for_restart` raises the server's answer instead of `AssertionError`."

## Report

- Behaviour / public API
  - `mlclient.exceptions.MLClientError` (new, exported); every library exception subclasses it.
  - `MarkLogicError.status_code | status | message_code | message`; `str(e)` unchanged.
  - `MLResponseParser.parse()` / `parse_with_headers()` raise for a non-success response (breaking); success
    parsing and the single-part collapsing (A6) are unchanged and now documented.
  - Manage health fallback, Cloud token exchange and the restart timestamp probe surface the MarkLogic error
    (`MarkLogicError` with `message_code`); no `AssertionError` any more.
- Files: `mlclient/exceptions.py`, `mlclient/responses.py`, `mlclient/_client.py`, `mlclient/auth.py`,
  `mlclient/clients/_restart.py`, `mlclient/services/{_execution,documents,search,transactions}.py`,
  `mlclient/services/diagnostics/log_level.py`, `docs/guides/clients.md`,
  `docs/advanced/health-and-administration.md`, tests (below).
- Tests added / changed
  - `test_exceptions.py`: fields, missing fields, raw message, Manage string status code, every exception is an
    `MLClientError`; `test_public_api.py` export list.
  - `test_responses.py`: the JSON / XML / HTML MarkLogic errors raise `MarkLogicError` (all output types, with
    and without headers); the C4 shapes (empty without Content-Type, text without Content-Type, invalid JSON,
    proxy HTML page, non-MarkLogic XML) raise `HTTPStatusError` with the original response; an XML error without
    `message-code` raises `MarkLogicError`. The old "error returned as a value" tests were replaced.
  - `test_client.py` / `test_async_client.py`: Manage fallback with a 403 `SEC-PRIV` body raises
    `MarkLogicError` (`message_code == "SEC-PRIV"`); the existing 403-without-error-body test still expects
    `HTTPStatusError`.
  - `test_cloud_auth.py`: a token rejection in the MarkLogic error format raises `MarkLogicError` (synthetic body;
    the existing 500-without-body test still expects `HTTPStatusError`).
  - `test_restart_waiter.py`: 403 `SEC-PRIV` -> `MarkLogicError` with the chained context, HTML 401 ->
    `HTTPStatusError` with the chained context, 204 -> `MLClientError`.
  - `test_transactions.py`: open with an empty 401 -> `HTTPStatusError`; open answered 204 -> `MarkLogicError`.
- Results: unit suite `10479 passed, 4 failed` with xdist. The 4 failures are not related to this branch:
  `test_logs_command.py::test_command_logs_all_hosts_reports_http_error[503-...]` fails on the base commit too
  (URL-encoding difference in the expected output); `test_main_sys_exit_1` and the two
  `test_job_is_explicitly_experimental` tests are order-dependent under xdist and pass when run on their own.
  Coverage of every touched module is 100% (the only gap, `cli/commands/_env_common.py:127-135`, is untouched
  code exercised by the order-dependent CLI test). Ruff check and format clean on touched files.
  `mkdocs build --strict` and `scripts/check_docs.py` pass (482 pages; built in a throwaway venv with the
  lock-file docs versions, since the shared venv has no docs group).
- Verified against local MarkLogic 12.1 (environment `local`, read-only requests): `parse()` of a missing
  document raises `MarkLogicError` 404 `RESTAPI-NODOCUMENT`; eval of a syntax error raises `MarkLogicError`
  `XDMP-BADCHAR`; eval `1+1` still parses to `2`; `_cluster_health_from_status` on Manage
  `view=nonsense` raises `MarkLogicError` 400 `REST-INVALIDTYPE` (status code converted from `"400"`) and on
  `view=healthcheck` returns a healthy verdict; `cluster_healthcheck()` healthy.
- Integration tests were not run locally (CI runs them on 10.0-11.1, 11.3.7 and 12.1).

## Open points for the reviewer

- Restart context is attached by chaining (`raise server_error from MLClientError(context)`) rather than wrapping,
  so callers keep catching `MarkLogicError` / `HTTPStatusError`. If the reviewer prefers the context in `str(e)`
  itself, it needs a wrapper exception (changes the raised type) or Python 3.11 `add_note`.
- `MarkLogicError.status_code` conversion to `int` (see above) goes slightly beyond A7a's wording; drop it if the
  raw value is preferred.
- The Cloud token endpoint error body used in the unit test is synthetic (MarkLogic error format); the real Cloud
  rejection body was not available. Any other body still gives `HTTPStatusError` as before.
