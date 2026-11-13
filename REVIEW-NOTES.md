# Review notes - feature/v1-07-timeout

## 1. Items

- B6. `--timeout SECONDS` for `eval`, `invoke`, `http`

## 2. Original plan

  - Decision: do, in `eval`, `invoke` and `http` only (not `sample`, `logs`, `version`, ...; no timeout in the
    environment YAML).
    - `--timeout SECONDS`: a number sets all four httpx components (connect, read, write, pool), as `timeout=<n>`
      does in the library; `0` disables the HTTP timeout (`timeout=None`); without the option the client default
      (`DEFAULT_TIMEOUT`) applies. Passed straight to the service call (`ml.eval.execute(..., timeout=...)`,
      `invoke`, the `http` request) - no new library code.
    - On `httpx.TimeoutException`: one line on stderr, e.g.
      `Request timed out after 60s - it may still be running on the server`, exit code 1, no stack trace.
    - Document the option and the "may still be running / an update may still commit" note in the help and the
      CLI docs.

## 3. What was added or changed around it

- The number in the message is the expired component of the timeout actually applied, read from
  `error.request.extensions["timeout"]` (`ConnectTimeout` -> connect, `ReadTimeout` -> read, ...). Without
  `--timeout` a read timeout says `60s`, a connect timeout `5s`; the effective value is reported, never a guess.
- Multi-environment runs (`-e a -e b`): a timed-out environment shows the same one-line message in its column
  instead of httpx's bare "The read operation timed out". This is done once in `_multi_env_common._run`, so it
  also applies to the other multi-environment commands (`health`, `version`, ...) when their request times out;
  those commands still have no `--timeout` option.
- `--timeout` is validated before any request: anything but a finite, non-negative number (`abc`, `-1`, `nan`,
  `inf`, empty) fails with `WrongParametersError` "--timeout must be a non-negative number of seconds, got: '-1'".
- The option definition, the parser and the message live in one new module, `mlclient/cli/timeout.py`, shared by
  the three commands (the existing `_execution_common.py` is eval/invoke only, and `http` needs it too).
- No library code changed; the commands pass `timeout=` straight to `ml.eval.execute`, `ml.invoke.module` and
  `ml.http.request` (UNSET when absent, None for 0, float otherwise).
- Docs: the "see what still runs" note is generic (Monitoring dashboard or `xdmp:server-status`), because the
  Management `requests` API (D4) lives on another branch.

## 4. Report

- CLI: `ml eval`, `ml invoke`, `ml http` accept `--timeout SECONDS` (number sets connect, read, write, pool;
  `0` disables; absent keeps connect 5 / read 60 / write 60 / pool 5). On `httpx.TimeoutException` the command
  prints one line to stderr, e.g. `Request timed out after 2s - it may still be running on the server`, and exits
  with 1, without a stack trace. The help text says a timed-out request may still run and an update may still
  commit.
- Files: `mlclient/cli/timeout.py` (new), `mlclient/cli/commands/{eval,invoke,http,_multi_env_common}.py`,
  `docs/cli/{eval,invoke,http}.md` (new `--timeout` section), `docs/advanced/http/timeouts.md` ("Command line"
  section), tests below.
- Tests (unit): `tests/unit/mlclient/cli/test_cli_timeout.py` (parsing: absent, numbers, 0, invalid values;
  message per timeout component) and a timeout section in `test_{eval,invoke,http}_command.py` per command: the
  timeout on the wire (`request.extensions["timeout"]`) for `--timeout 2`, `0` and absent, single and
  multi-environment; the one-line stderr message and exit 1; the message in the multi-environment column; an
  invalid value rejected before any request.
- Results: full unit suite 10460 passed (serial run). `ruff check .` clean; `ruff format --check` clean for the
  new files (two test files touched here have pre-existing format differences in untouched lines, left as they
  were). `mkdocs build --strict` and `scripts/check_docs.py` pass.
- Integration tests: none added (the behaviour is CLI-only and covered by unit tests with the real httpx
  request extensions); nothing run against the CI matrix locally.
- Verified against local MarkLogic 12.1 (environment `local`), with this branch's code:
  - `ml eval -x 'xdmp:sleep(5000), "slept"' --timeout 2` -> `Request timed out after 2s - it may still be
    running on the server`, exit 1;
  - the same eval with `--timeout 0` and `--timeout 10` -> `slept`, exit 0;
  - `ml http post /v1/eval ... -b 'xquery=xdmp:sleep(5000)' --timeout 1.5` -> `Request timed out after 1.5s
    ...`, exit 1;
  - `ml eval -x 1 --timeout=-3` -> the validation message, exit 1;
  - an update (`xdmp:sleep(4000), xdmp:document-insert("/mlclient-v1-07/commit-check.xml", ...)`) with
    `--timeout 1` timed out on the client and the document existed afterwards - the documented "an update may
    still commit" confirmed; the test document was deleted.
  - `ml invoke` was not run live (no test module installed locally); its path is the same as eval's and is unit
    tested.

## 5. Open points for the reviewer

- `ml http get|head|put|delete`: with the current default retry strategy a `ReadTimeout` is retried up to 5
  times, so the command can wait several times `--timeout` before reporting it (the message names one
  timeout). C2 (another branch) drops `ReadTimeout` from the default retry, which resolves this; no change here.
- A `ConnectTimeout` gets the same message ("may still be running on the server") although such a request never
  reached MarkLogic. Kept to the decided single message; say if connect timeouts should read differently.
- After D4 merges, the docs note could point at `ml.manage.requests.get_list(seconds_min=...)`.
- `--timeout -1` is parsed by cleo as an option; a negative value must be written `--timeout=-1` to reach the
  validation (cleo behaviour, not specific to this option).
