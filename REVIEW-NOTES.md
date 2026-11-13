# Review notes - feature/v1-06-cli-http

## Items

- B3. `ml http` sends `rs:view=x` as a header `rs: view=x`
- B4. `ml http -b @file` has no default Content-Type
- B5. `ml http` on an error status prints an httpx traceback after the body

## Original plan

B3:

  - Decision: do - a list of known prefixes only. In `_parse_params` (`cli/commands/http.py:244`), a token that
    starts with `rs:`, `trans:`, `perm:`, `prop:`, `value:`, `bind:`, `get:`, `put:`, `post:` or `delete:` and
    contains `=` is a query parameter; every other token keeps today's rule (first of `=` / `:` decides). No
    general "colon before equals" rule - it would break headers such as
    `Content-Type:multipart/mixed; boundary=xyz`. No extra `-P` switch. Mention the prefixes in the `http` help.

B4:

  - Decision: do. When `-b` points to a file (path or `@path`) and no `Content-Type` header was given, set it from
    the file extension with the existing `Mimetypes.get_mimetype(path)` (`models/mimetypes.py:57`, MarkLogic's own
    table in `resources/mimetypes.yaml`), not the stdlib `mimetypes`. An explicit `Content-Type` always wins; a
    literal body (`-b '{"a":1}'`) and an extension unknown to the table get no header, as today.

B5:

  - Decision: do. Replace `response.raise_for_status()` (`cli/commands/http.py:148-149`):
    - error with a body: print the body (stdout) and return exit code 1, nothing else;
    - error with an empty body (`not response.content`): print one status line with the URL to stderr, e.g.
      `HTTP 503 Service Unavailable for https://marklogic.example.com:8010/v1/ping`, exit code 1 - no
      MDN link, no stack trace;
    - `HEAD` / `--include`: the status line is already in the output, add nothing;
    - multi-env (`_request_in_environments`): an empty error body puts the same status line into the
      environment's column instead of an empty cell.

## What was added or changed around it

- B4: the mimetype is looked up with the file name (`Mimetypes.get_mimetype(path.name)`). The table lookup is
  case-sensitive (`doc.JSON` gets no header), kept as is - it is the existing library behaviour.
- B5: "empty error body" is decided on the rendered output (`not output`) rather than on `response.content`.
  It is the same condition for a plain request (empty content renders as an empty string), and it covers
  `HEAD` / `--include` automatically because their output always starts with the status line. The empty stdout
  line printed before is no longer printed in that case.
- B5: the class docstring gained one sentence on the exit code of an error response; `docs/cli/http.md`
  ("Responses and errors", `params`, `--body`, examples) describes all three changes. The PUT XML example no
  longer passes `Content-Type:application/xml` because the file extension now sets it.
- Help: the prefixes are listed in the `params` argument description (shown by `ml http --help`), and the
  `--body` option description says a file's extension sets the default Content-Type.

## Report

- Changed: `mlclient/cli/commands/http.py`
  - `_parse_params`: a token starting with one of `_QUERY_PARAM_PREFIXES` (`rs:`, `trans:`, `perm:`, `prop:`,
    `value:`, `bind:`, `get:`, `put:`, `post:`, `delete:`) and containing `=` is a query parameter; every other
    token keeps the first-of-`=`/`:` rule.
  - `_read_body` returns the body and the MarkLogic mimetype of a file body's extension; `handle` sets it as
    `Content-Type` only when no `Content-Type` header (any case) was given.
  - `raise_for_status()` removed: an error with a body prints the body and exits 1; an error with an empty body
    prints `HTTP <code> <reason> for <url>` to stderr and exits 1; multi-env shows that line in the
    environment's column. New helper `_status_line`.
- Docs: `docs/cli/http.md`.
- Tests: `tests/unit/mlclient/cli/commands/test_http_command.py` - 25 new or rewritten cases (all prefixes
  incl. `bind:name:type` / `bind:name@lang` and extension declarations; colon tokens that stay headers incl.
  `Content-Type:multipart/mixed; boundary=xyz`; Content-Type from `.json` for path and `@path`; explicit
  header wins in either case; unknown / missing extension and literal body get none; error with body, error
  without body on stderr, `--include` and `HEAD` errors, multi-env empty error body). The two tests that
  expected `HTTPStatusError` now expect exit code 1.
- Results: `test_http_command.py` 67 passed. Full `tests/unit`: 10442 passed, 8 failed; the same 8 fail on the
  untouched base `7fa179304` with the shared venv (see Open points). Ruff check and format clean for the
  touched lines.
- Integration tests: none added (the decision asks for none; the command is covered by unit tests with respx).
- Verified against local MarkLogic 12.1 (environment `local`), documents under `/mlclient-v1-06/` removed
  afterwards:
  - `put ... -b @doc.json` without a header to an extensionless URI is stored as JSON; with
    `Content-Type:text/plain` as text (explicit header wins).
  - `perm:rest-reader=read prop:mlclient-v1-06=yes` on PUT set the permission and property (read back with
    `category=permissions category=properties`); `perm:x=y` on GET reaches the server as a query parameter
    (`REST-UNSUPPORTEDPARAM ... perm:x`).
  - `GET` of a missing document prints the `RESTAPI-NODOCUMENT` body, exit 1, no traceback.
  - `GET /v1/nonexistent-endpoint-v1-06` (empty 404 body) prints
    `HTTP 404 Not Found for http://localhost:<port>/v1/nonexistent-endpoint-v1-06` on stderr, exit 1.
  - `HEAD` of a missing document prints the status line and headers, exit 1.
  - Multi-env was not verified against a server (only one environment may be used); covered by a unit test.

## Open points for the reviewer

- Pre-existing unit failures with the shared venv, unrelated to this branch (identical on the base commit):
  `test_logs_command.py::test_command_logs_all_hosts_reports_http_error[503-...]` (URL encoded with `+` vs
  `%20`, fails alone too), and seven tests that fail only in the full run (`jobs/*::test_job_is_explicitly_experimental`,
  `services/diagnostics/test_log_level.py` fallback/timeout cases, `test_auth.py::test_kerberos_mutual_auth_warns_without_server_token`)
  and pass when run on their own - looks like test-order dependence around warnings/logging.
- The `params` help line is long (one line in `ml http --help`); move the prefix list to a command `help`
  text if preferred.
