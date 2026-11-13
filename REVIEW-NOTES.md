# Review notes

## Items

- B7. `ml eval '1+1'` without `-x` says only "Unknown file extension!"

## Original plan

  - Decision: do - default to XQuery instead of the hint. CLI only (`_build_params` in `cli/commands/eval.py`); the
    library's explicit `xq` / `js` / `file` parameters stay. Rules for an argument without `-x`/`-j`:
    | Argument | Result |
    |---|---|
    | `@path` | file; error if it does not exist (same as `ml http -b @path`) |
    | an existing file with a code extension (`services/eval.py:19-20`: xq, xql, xqm, xqu, xquery, xqy, js, sjs) | file, language from the extension |
    | an existing file with another extension (`notes.txt`) | error "Unknown file extension", as today |
    | a non-existing name ending with a code extension (`quer.xqy`) | error "File not found" - a typo must not run as XQuery |
    | anything else (`'1+1'`, `'fn:doc("/a.json")'`) | XQuery code, as with `-x` |
    - `-x` / `-j` keep treating the argument as code, even when it looks like a path.
    - Update the `eval` help and docs.

## What was added or changed around it

- The method is `_get_eval_params` (the checklist names it `_build_params`); the detection lives in a new
  module-level helper `_detect_code_source` it calls, plus `_is_file`.
- The code extension check uses a dot (`.xqy`, `.sjs`, ...). The library's `_file_language` matches the bare
  suffix (`endswith("js")`), which would have turned inline code such as `... return $objs` into a
  "File not found" error.
- Inline code too long to be a file name (`OSError: File name too long` from `Path.is_file`) is treated as
  code, like `ml http -b` does.
- `_SUPPORTED_FILE_EXT` in `mlclient/services/eval.py` was renamed to `SUPPORTED_FILE_EXTENSIONS` so the CLI
  can reuse the list without importing a private name. Not added to any `__all__`; library behaviour unchanged.
- "File not found" and a missing `@path` raise `WrongParametersError` (as other CLI argument errors do),
  before any request. "Unknown file extension" still comes from the service (`UnsupportedFileExtensionError`).

## Report

- Behaviour: without `-x`/`-j`, `ml eval` follows the decision table; `-x`/`-j` unchanged (always code).
- Files: `mlclient/cli/commands/eval.py`, `mlclient/services/eval.py` (constant rename),
  `tests/unit/mlclient/cli/commands/test_eval_command.py`, `docs/cli/eval.md` (rules table, `-x`/`-j`
  wording, first example now runs without `-x`). The argument help now reads
  "XQuery code, a code file path, or @path to force a file".
- Tests: 15 new unit tests (inline XQuery, `$objs` suffix without dot, over-long code, existing `.sjs`,
  explicit `@file`, missing `@path` incl. bare `@`, missing names with code extensions, `notes.txt` and
  `@notes.txt`, `-x`/`-j` with an existing file path). Full unit suite: 10440 passed; `mlclient/cli/commands/eval.py` fully covered; ruff check and format clean;
  `mkdocs build --strict` and `scripts/check_docs.py` pass.
  No integration tests added (the decision is CLI argument parsing; no server behaviour changed).
- Verified against local MarkLogic 12.1 with the worktree code (`ml eval` via the shared venv,
  `PYTHONPATH` = worktree): `@q.xqy` -> 42; `@missing.xqy` -> File not found; `q.xqy` -> 42;
  `q.sjs` -> js-2; `notes.txt` and `@notes.txt` -> Unknown file extension; `quer.xqy` -> File not found;
  `1+1` -> 2; `fn:doc-available("/a.json")` -> false; `let $objs := (1,2) return count($objs)` -> 2;
  `-x /path/q.xqy` -> sent as code (server syntax error); `-j '1+2'` -> 3.

## Open points for the reviewer

- XQuery starting with `@` (an attribute path such as `@id`) is now read as a file reference; it needs `-x`.
  This follows the decision and has no context node in eval anyway.
- `docs/assets/gifs/eval.tape` still uses `-x`; it remains valid, so the GIF was not re-recorded.
