# Review notes - feature/v1-02-typing

## Items

- A4. Add `py.typed`
- A5. Return type hints on the most visible public methods (full typing review, `ANN` in ruff)

## Original plan

A4 - Decision: do. No dependency and no version change - a PEP 561 marker file only.
- Add an empty `mlclient/py.typed` (empty = the whole package has inline hints; `partial` is only for stub
  packages).
- `pyproject.toml`: `include = ["mlclient/resources/*", "mlclient/py.typed"]` (explicit, even if poetry would
  pick it up anyway) and the classifier `"Typing :: Typed"`.
- Verify: `poetry build` puts `mlclient/py.typed` in the wheel; mypy on a script with
  `from mlclient import MLClient` no longer reports "missing library stubs or py.typed marker".
- Hints become part of the contract; gaps show up to users as `Any` (see A5).

A5 - Decision: do the full review (M) - the public API must be well typed, not only the listed groups.
- Every public function and method gets precise parameter and return types: no bare `Any` where a concrete
  type is known, `-> None` / `-> Self` where applicable, `auth_flow` as
  `Generator[httpx.Request, httpx.Response, None]`, sync and async variants typed alike.
- Check: `ruff --select ANN201` reports nothing for public functions.
- Enforce it: add `"ANN"` to `lint.select` in `pyproject.toml`, so the lint job in CI rejects new functions
  without annotations (see also E).

## What was added or changed around it

- The sweep covers every function in `mlclient/` (public and private), so the full `ANN` rule set passes,
  not only `ANN201`.
- `tests/*` gets a per-file ignore for `ANN`: about 11k test functions and fixtures are not public API.
- Keyword arguments with a fixed key set are typed with `Unpack[TypedDict]` (from `typing_extensions`, imported
  under `TYPE_CHECKING` only, since Python 3.10 is supported). The TypedDicts live under `TYPE_CHECKING` too,
  so nothing is added at runtime:
  - `services/cts.py`: `_ExecutionOptions` (database, txid, timeout, namespaces) and
    `_NativeExecutionOptions` (+ output_type) for the ~200 cts service methods.
  - `http.py`: `_HTTPConfigOverrides` for `HTTPConfig.clone(**overrides)` and all `MLClientManager` methods.
  - `_client.py`: `_MLClientOptions` for `DocumentsWriteJob/ReadJob.with_client_config(**config)`.
  - `clients/http.py`: `_HttpClientOptions` for `HttpClient/AsyncHttpClient.__init__(**kwargs)`.
- Eval/invoke `**kwargs` (external variables, JSON-encoded) are `object`.
- Existing imprecise annotations fixed on the way: `__exit__`/`__aexit__` arguments now `... | None`,
  `__subclasshook__(subclass: type) -> bool`, `__enter__/__aenter__ -> Self` on `MLClient`, `AsyncMLClient`,
  `HttpClient`, `AsyncHttpClient` (so `with MLClient() as ml` types `ml`), and `Any` replaced where the type is
  known (`ApiCall.add_param/add_header`, `Document.content`, `_BiDict.get`, documents parsing). The numpy
  docstring types were updated where they said `Any`.
- `Any` remains only in two FINE-logging forwarders (`**kwargs` passed to `Logger.log`), with a `noqa: ANN401`.
- Defaults of `UNSET` keep the caller-facing type without `_Unset` (existing convention, e.g.
  `database: str | None = UNSET`); private helpers that receive `UNSET` include `_Unset`.
- The `mlclient/xquery` part was done by a sub-agent of this branch under the same rules and reviewed here.

## Report

- Behaviour: none changed. Verified by an AST comparison of all 77 changed modules against `7fa179304` with
  annotations, docstrings, imports and `TYPE_CHECKING` blocks stripped - all identical.
- Public API: annotations only; `mlclient/py.typed` ships in the wheel (checked with `poetry build`).
- Files: `pyproject.toml`, `mlclient/py.typed`, 77 modules under `mlclient/`.
- Lint: `ruff check .` passes with `ANN` selected; `ruff format --check` clean for touched files (two untouched
  test files were already unformatted on `main`).
- Tests: `tests/unit` - 10425 passed. No tests added (annotations only; nothing at runtime to test).
  Integration tests not needed / not run.
- mypy smoke check (mypy in a throwaway uv venv, wheel installed): with the base wheel
  `from mlclient import MLClient` reports "missing library stubs or py.typed marker"; with this branch's wheel
  it passes. `with MLClient() as ml` reveals `MLClient`, `ml.eval.xquery(...)` reveals the parsed-value union,
  and `CtsService(...).uris(database=1)` is rejected (`Unpack` kwargs are checked).

## Open points for the reviewer

- `mypy mlclient` on the library itself is not clean (975 errors on `main` already, mostly `arg-type`,
  `assignment` and `override`); making it clean was not in scope. One cause: `UNSET` defaults sit outside
  their declared type (`str | None = UNSET`). Fixing it means exposing the sentinel type publicly - decide
  whether that is wanted.
- `AtomicInput` / `NodeInput` in `xquery/expressions.py` use `list[...]`, which mypy treats as invariant, so a
  `list[str]` is not accepted where `list[AtomicInput]` is expected. Switching the list branches to
  `Sequence[...]` would fix it for users; left as is (alias change, wider than annotations).
- `typing_extensions` is used only under `TYPE_CHECKING` (for `Self`, `Unpack`); it is not a declared
  dependency but comes with pydantic. Declare it explicitly if preferred.
- `CtsService.uris` / `uri_match` accept `output_type` at runtime (typed as such) but their docstrings list
  only database, txid, timeout and namespaces.
