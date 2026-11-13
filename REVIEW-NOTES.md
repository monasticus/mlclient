# Review notes - feature/v1-05-cli-output-streams

## Items

- B1. `Evaluating code using REST App-Server ...` header goes to stdout (all four points)

## Original plan

  - Decision: do. Rule: stdout carries only the command's result (eval/invoke results, the MarkLogic log lines of
    `ml logs`, ...); messages about the tool itself go to stderr.
    1. The header (`eval.py:207`, `invoke.py:136`, `logs.py:189`) becomes `logger.info(...)` instead of
       `self.info(...)`, so it shows only with `-v` (the existing `CleoAppHandler` level mapping).
    2. `CleoAppHandler.emit` (`cli/app.py`) writes with `io.write_error_line` instead of `io.write_line`, so all
       mlclient / CLI logs go to stderr. Keep the colours: `setup_for` registers the `mlclient_*` styles on
       `io.error_output.formatter` as well as on `io.output.formatter` (cleo keeps a separate formatter per stream).
       This affects the `ml` CLI only - library users never get this handler. Leave `resources/logging.yaml` as is.
    3. Remove the blank line before results (`_execution_common.py:70`, and `self.line("")` before the log lines
       in `logs.py:339`).
    - Unaffected: the colours of `ml logs` output (`<time>`, `<log-level>` styles registered in `create_io`,
      `cli/app.py:83-85`, and per-host colours) belong to the result on stdout, not to the log handler.
    4. A waiting indicator while the request runs (cleo `ProgressIndicator`, e.g. `Waiting for <url> ... 2.4s`):
       on stderr, only when stderr is a terminal (`is_decorated()`), cleared before the result is printed.
       Redirecting stdout (`> file`, `| jq`) keeps a clean result; `2> file`, CI and scripts get no indicator.
       Effort M.
       - Covers every single-environment command that calls MarkLogic: `eval`, `invoke`, `http`, `logs`, `sample`,
         `version`, `log-level`, `trace-events` - consistent with the waiting display of multi-env runs.
       - One shared helper used by all of them, not per-command code.
       - Not shown where a command already has its own live display (`health --watch`, multi-env tables) or while
         it waits for user input (`trace-events -i` prompts).
       - `url` makes no request and gets none.

## What was added or changed around it

- **Also the `invoke` and the other `logs` headers.** Besides the three named lines, `Invoking module using
  REST App-Server ...` (invoke), `Getting logs list ...` (`logs --list`) and `Getting error logs from every
  host ...` (`logs --all-hosts`) became `logger.info` too, and the blank line was removed before every result
  of `logs` (single file, `--list`, `--all-hosts`), not only at `logs.py:339`.
- **Log lines erase the indicator line.** At `-v` the library logs `Sending a request...` while the indicator is
  on screen, and some warnings are logged at normal verbosity during a request. Without care the log text is
  glued to the end of the spinner line. `CleoAppHandler.emit` therefore prefixes `\r\x1b[2K` (erase the current
  line) when stderr is decorated; the spinner redraws on the next tick below the log line.
- **Indicator format.** `- Waiting for http://localhost:8002 2.4 s` (spinner, URL, seconds with one decimal and
  the `comment` style), matching the `2.4 s` counter of the multi-env tables. Implemented in
  `mlclient/cli/commands/_waiting_indicator.py` as the context manager `waiting_for(io, url)`: cleo
  `ProgressIndicator` for drawing, a daemon thread refreshing every 0.1 s, line erased in `finally` (also on
  errors and Ctrl-C). Nothing is written when stderr is not decorated or in `-q`.
  cleo's `ProgressIndicator.auto()` was not used: it ends with a newline (leaves the line) instead of erasing it.
- **trace-events -i.** The indicator wraps the initial read and the saving of the selection, not the prompt.
  The saving loop moved into a new `_apply_selection` method so it can be wrapped in one block.
- **Side effect worth knowing:** library warnings (e.g. `Basic auth over HTTP sends credentials in cleartext`)
  were printed on stdout before and polluted results; they now go to stderr.
- **Formatter noise.** `ruff format` reformatted two pre-existing unformatted spots in `test_http_command.py`
  and `test_invoke_command.py` (the files were touched anyway).
- **Docs.** New "Output streams" section in `docs/cli/index.md`; the `-v` option there mentions the App Server line.
  No changelog file exists in the project.
- **Stash incident (no effect on the result).** `git stash` is shared by all worktrees of the repository. While
  checking a flaky test, this branch's agent stashed its work at the same time as the v1-10 agent; each popped
  the other's stash. Both trees were restored: v1-10 restored its own tree; here the foreign changes were
  discarded with `git checkout -- .` and this branch's stash commit `123bf07` was re-applied with
  `git stash apply 123bf07`. Verified with `git diff 7fa179304 --stat` (only B1 files) and
  `grep -rn "_log_file_name\|creates it" mlclient tests docs` (no B9 code). `git stash` was not used again.

## Report

- Behaviour: stdout carries only results for `eval`, `invoke`, `http`, `logs`, `sample`, `version`,
  `log-level`, `trace-events`; headers are `logger.info` (stderr, `-v` only); all `ml` log output goes to stderr
  with the `mlclient_*` styles on both formatters; no blank line before results; waiting indicator on a terminal
  stderr for the single-environment path of the eight commands (not for multi-env tables, `health`, `url`,
  prompts). No public library API change.
- Files: `mlclient/cli/app.py`, `mlclient/cli/commands/{_waiting_indicator (new), _execution_common, eval, invoke,
  http, logs, sample, version, log_level, trace_events}.py`, `docs/cli/index.md`, tests under
  `tests/unit/mlclient/cli/` (new `conftest.py` with the `mlclient_logger` fixture, new
  `commands/test_waiting_indicator.py`, updated command tests), and nine `test-logs-command/output-*.txt`
  resources (header and blank line removed).
- Tests: per command, indicator shown on a decorated stderr with stdout exactly the result and the line erased at
  the end; nothing on stderr when it is not a terminal; header on stderr only with `-v` (eval, invoke, logs via
  `ApplicationTester`, i.e. the real `create_io` / `CleoAppHandler` path); handler writes to stderr, hides INFO
  without `-v`, erases the line, styles rendered on stderr; indicator helper (erased on exit and on exception,
  counter advances, silent when not decorated or quiet); trace-events `-i` indicator erased before the prompt.
  Unit suite: 10458 tests, all pass (`test_main_sys_exit_1` fails only under `pytest -n`, since it
  depends on `sys.argv`; it passes serially). `mlclient/cli` coverage 100% except the untouched
  `_env_common.py:127-135` (covered by tests outside `tests/unit/mlclient/cli`). Ruff check and format clean.
  `mkdocs build --strict` and `scripts/check_docs.py` pass. No integration tests were needed (CLI only).
- Verified against local MarkLogic 12.1 (`local`): all eight commands with stdout redirected print only the result
  and nothing on stderr; `eval -v` prints the App Server line on stderr only; under a pseudo-terminal
  (`script`) `eval -x 'xdmp:sleep(400), 42' > out` shows the spinner with the URL and counter on the terminal
  while `out` holds only `42`.

## Open points for the reviewer

- The log handler erases the current stderr line before each log record when stderr is decorated. That is what
  keeps log lines from sticking to the indicator; it would also erase any other unfinished stderr line, but the
  CLI writes none (prompts end with the user's Enter before anything is logged).
- The spinner thread draws each tick with two writes (`set_message`, then `advance` to rotate the spinner);
  invisible in practice, mentioned only because it relies on `ProgressIndicator(interval=0)`.
