# Review notes - feature/v1-16-logs-text-format

## Items

- D2. `/manage/v2/logs` rejects `format=text`

## Original plan

- Decision: do.
  - `LogsCall._validate_params` (`calls/logs.py:96`): allow `"text"`; message "The supported formats are xml,
    json, html or text!". The Accept mapping (`text/plain`) already exists.
  - Docstrings of `data_format` in `LogsCall` and the logs API methods (sync and async) list `text`.
  - `ml logs` and `services/diagnostics/logs.py` unchanged (they keep JSON).
  - Tests: unit - `data_format="text"` gives `Accept: text/plain` and `format=text`; integration (CI matrix) -
    `format=text` with `regex` returns `text/plain` lines that all match.

## What was added or changed around it

- The existing unit test `test_validation_unsupported_format` used `"text"` as its unsupported example; it now
  uses `"csv"` and expects the new message.
- Besides the Call-level unit tests, one sync and one async API-level unit test (`ml.manage.logs.get(...,
  data_format="text")`) check that the request carries `format=text` and `Accept: text/plain` and that the
  plain-text body comes back as is.
- No docs page or changelog change: the decision names none, the guides do not list the logs formats, and the
  repository has no changelog.

## Report

- Behaviour: `LogsCall(..., data_format="text")` and `ml.manage.logs.get(..., data_format="text")` (sync and
  async) now send `format=text` with `Accept: text/plain` and return the raw log lines. Other unsupported formats
  raise `WrongParametersError: The supported formats are xml, json, html or text!`. `ml logs` and
  `services/diagnostics/logs.py` are unchanged (JSON).
- Files: `mlclient/calls/logs.py`, `mlclient/api/logs.py` (docstrings of both `get` methods),
  `tests/unit/mlclient/calls/test_logs_call.py`, `tests/unit/mlclient/api/test_manage_api.py`,
  `tests/unit/mlclient/api/test_async_manage_api.py`, `tests/integration/mlclient/clients/test_api_wrappers.py`.
- Tests: unit suite 10429 passed (4 new tests: text Accept header, text params, sync and async API text
  request). Ruff check and format clean for the touched files.
- Integration: `TestLogs.test_error_logs_as_text_contain_only_lines_matching_regex` writes 10 `xdmp:log`
  entries and requests the App Server's ErrorLog with `format=text` and `regex`; asserts `text/plain` and that
  every line matches. Not run locally - CI runs it on MarkLogic 10.0-11.1, 11.3.7 and 12.1.
- Verified against local MarkLogic 12.1 through the worktree code (`MLClientManager("local").get_client("manage")`,
  `ml.manage.logs.get(filename="ErrorLog.txt", data_format="text", start_time=today, regex="Merged")`):
  200 `text/plain; charset=UTF-8`, 215 lines, every one matching `Merged`.

## Open points for the reviewer

- None.
