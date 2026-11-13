# Review notes - feature/v1-10-logs-missing-file-hint

## Items

- B9. `MANAGE-NOSUCHLOG` for `ml logs -s <server>` is unexplained

## Original plan

Decision: do - a hint only. When the logs request fails with 404 `MANAGE-NOSUCHLOG`, keep the MarkLogic
error as it is and add one line to stderr, exit code stays 1:
`No {filename} yet - MarkLogic creates it when the server first logs something. Run 'ml logs --list' to see the existing log files.`
where `{filename}` is the requested log file (e.g. `No 8010_ErrorLog.txt yet - ...`, `No 8002_AccessLog.txt yet - ...`). No check whether the server exists, no "empty log = success".

## What was added or changed around it

- Paths covered: the single-host read (any log type, any `-s`, with or without `-H`) and `--all-hosts`.
  `ml logs` has no multi-environment mode (`-e` takes one environment), and `--list` sends no file name, so
  neither can hit `MANAGE-NOSUCHLOG`.
- Single-host: the command catches the `MarkLogicError`, renders it through the application's own
  `render_error` (so the output is identical to before, including the full trace with `-v`), prints the hint
  and returns 1. Any other `MarkLogicError` is still raised unchanged.
- `--all-hosts`: the per-host reasons are printed as before; the hint is printed once after the
  "missing hosts" list when at least one host failed with `MANAGE-NOSUCHLOG`. Exit code stays 1.
- Refactor in `logs.py` needed for the hint: the log file name is built once in a `_log_file_name` helper
  (used for the progress message and the hint), and the App Server port is resolved by the callers
  (`_print_logs`, `_print_logs_all_hosts`) and passed down, so the file name is known where the error is
  handled.
- Docs: `docs/cli/logs.md` (`--server` section) explains the missing file, the hint and the exit code.

## Report

- Behaviour: `ml logs -s <port>` for a log file MarkLogic has not created yet prints the unchanged
  MarkLogic error plus the hint line on stderr and exits 1. Same for `--all-hosts` after the missing-hosts
  summary. No public API change.
- Files: `mlclient/cli/commands/logs.py`, `tests/unit/mlclient/cli/commands/test_logs_command.py`,
  `docs/cli/logs.md`.
- Tests added (unit): hint for `8010_ErrorLog.txt`, `8002_AccessLog.txt` and the main `ErrorLog.txt`
  (exact stderr, exit 1); another MarkLogic error (403 `SEC-PRIV`) is still raised without a hint;
  `--all-hosts` with two hosts both missing the file prints the hint exactly once.
  Full unit suite: 10430 passed. Ruff check and format clean on touched files. No integration tests added
  (the decision asks for none); none were run locally.
- Verified against local MarkLogic 12.1 (environment `local`) with the worktree code:
  - `ml logs -e local -s 3703` (App Server with access and request logs, no `3703_ErrorLog.txt`): MarkLogic
    error, then `No 3703_ErrorLog.txt yet - ...`, exit 1.
  - `ml logs -e local -s 3703 -v`: full cleo trace as before, followed by the hint, exit 1.
  - `ml logs -e local -s 3703 --all-hosts -r needle`: missing-hosts summary, then the hint, exit 1.
  - `ml logs -e local -s 3700` (existing file): unchanged, exit 0.

## Open points for the reviewer

- The error is recognised by its message (`[404 ` prefix and `(MANAGE-NOSUCHLOG)`) because
  `MarkLogicError` has no structured fields on `main` yet. Once A7a (`status_code` / `message_code` on
  `MarkLogicError`) is merged, `_is_missing_log` should switch to `message_code == "MANAGE-NOSUCHLOG"`;
  in `--all-hosts` the failures are kept as strings today, so that switch also means keeping the error
  objects there.
