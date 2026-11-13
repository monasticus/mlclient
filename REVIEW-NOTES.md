# Review notes - feature/v1-09-config-dir-lookup

## Items

- B8. `.mlclient` not found: message lacks cwd, no `~/.mlclient` fallback

## Original plan

- Decision: do both, in the library (`find_mlclient_directory`, so `MLClientManager` gets it too, not only the
  CLI).
  - Fallback: when no `.mlclient` exists in cwd or any parent, use `Path.home() / ".mlclient"` if it is a
    directory. Log the source at debug level (shown with `ml -v`), e.g.
    `Using global configuration directory [~/.mlclient]`, in the spirit of `announce_source`
    (`cli/commands/_env_common.py`).
  - Message when neither exists names the start directory and the next step, e.g.
    `.mlclient directory has not been found in /tmp or any of its parents (nor in ~/.mlclient). Run 'ml env init' or 'ml env init --global'.`
  - Unchanged: a `.mlclient` found in cwd or a parent still wins over the home one; `ml env --global` keeps
    pointing at `~/.mlclient`.

## What was added or changed around it

- **The walk now checks `/.mlclient` too.** The old recursion stopped at `/` (and at `.` for a relative path)
  before looking there, so the root directory was never searched. The new loop goes over the start directory and
  all of its `parents`, root included. This matters little in practice (nobody keeps configuration in `/`), but
  "cwd or any of its parents" now means exactly that, and in containers where the working directory is `/` a
  `/.mlclient` is found. Kept because it is the natural result of the simpler loop, not a special case.
- **Relative start paths are made absolute** (`path.absolute()`) before the walk. Before, `Path(".")` stopped
  immediately without searching anything above cwd; now a relative path searches up to the root like an absolute
  one, and the error message always names an absolute directory.
- **Messages show real paths, not `~`.** Both the debug log and the error print the resolved home path (e.g.
  `/home/me/.mlclient`), because `HOME` may differ from what the user assumes (CI, sudo, containers).
- **`ml env show|copy|edit|remove|compare` without `--global`** go through `resolve_env_dir` ->
  `find_mlclient_directory`, so outside the home tree they now also fall back to `~/.mlclient` instead of the
  non-existing `./.mlclient`. This is the same "implicit fall-through to global" these commands already had
  when cwd is under home, and `announce_source` already labels it `(global)`. `ml env init` does not use the
  lookup and still writes to cwd unless `--global` is given.
- **Test isolation from the real home directory.** The autouse `_work_dir` fixtures of the five `env` command
  test modules now also patch `Path.home` to a non-existing `tmp_path / "home"`; without it three tests found the
  developer's real `~/.mlclient`. All new `find_mlclient_directory` tests patch `Path.home` as well.

## Report

- Behaviour: `find_mlclient_directory(path)` (`mlclient/env.py`) returns the nearest `.mlclient` directory at
  `path` or any parent (root included); otherwise `Path.home() / ".mlclient"` when it is a directory, logging
  `Using global configuration directory [<path>]` at debug level; otherwise raises
  `MLClientDirectoryNotFoundError` with
  `.mlclient directory has not been found in <start> or any of its parents (nor in <home>/.mlclient). Run 'ml env init' or 'ml env init --global'.`
  A file (not a directory) named `.mlclient` is ignored, as before. No public API signature changed.
- Docs: `docs/guides/environments.md` (manager lookup) and `docs/cli/env/show.md` (lookup used by all `env`
  commands) mention the home fallback.
- Files: `mlclient/env.py`, `tests/unit/mlclient/test_env.py`,
  `tests/unit/mlclient/cli/commands/test_env_{show,copy,compare,edit,remove}_command.py`, the two docs pages.
- Tests added: home fallback with debug log, ancestor wins over home, a home *file* named `.mlclient` is
  ignored, relative start path searches above cwd, the new not-found message, `env show` from a directory
  outside home falls back to global and is labelled `(global)`. Existing not-found tests now isolate home.
- Unit suite: full `tests/unit` 10430 passed (5 new tests). Ruff check and format clean
  for touched files.
- Integration tests: none added - the change is a filesystem lookup with no server interaction.
- Verified against local MarkLogic 12.1 from a directory outside home: `ml -vvv eval -e local -x '1+1'` logs
  `Using global configuration directory [/home/<user>/.mlclient]` and returns `2`; with `HOME` pointing at an
  empty directory it prints the new message and exits 1.

## Open points for the reviewer

- Confirm that searching `/.mlclient` (now included in the walk) is wanted; excluding it would need an explicit
  special case.
- Confirm that the `env` commands (other than `init`) falling back to `~/.mlclient` outside the home tree is the
  intended consequence of putting the fallback in the library (the decision put it there deliberately).
