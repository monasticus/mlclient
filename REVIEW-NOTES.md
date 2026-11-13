# Review notes - feature/v1-01-dependencies

## Items

- A1. Widen dependency upper bounds
- A2. xmltodict 1.x returns an `@xmlns` key that breaks `Metadata.from_xml_file`
- A3. httpx 0.28 encodes query spaces as `%20`, not `+`

## Original plan

A1:

> Decision: do. Keep the lower bounds, lock and develop on the latest versions. `httpx-retries<0.7` (not `<1`):
> `httpx_retries.Retry` is part of the public API (`MLClient(retry=...)`), so each new 0.x minor is checked and
> the bound raised by hand. Add a CI job that installs the lowest direct versions (`lowest-direct`) and runs
> against MarkLogic 12.
> - Final bounds: `httpx>=0.27.0,<1.0.0`, `xmltodict>=0.13.0,<2.0.0`, `aiofiles>=24.1.0,<26.0.0`,
>   `httpx-retries>=0.4.5,<0.7.0`; dev `respx = "^0.22"`; then `poetry lock` (resolves to the latest versions).
> - `pyspnego[kerberos]>=0.12.1,<0.13.0` (kerberos extra) stays - the latest release is 0.12.4.
> - Checked compatible: httpx 0.28 deprecates `verify=<path>` and `cert=`, but mlclient always passes an
>   `SSLContext` or `False` (`connection.py:297`, also to the Cloud token flow).

A2:

> Decision: do, with a `postprocessor` in `xmltodict.parse` that skips the `@xmlns` key (a named method, not a
> lambda). It drops default and prefixed declarations at every depth; `xml_attribs=False` is not an option
> because the parser reads `@key` of `metadata-value`. Works on xmltodict 0.13 and 1.x.

A3:

> Correction: httpx 0.27 gives `%20` (matches `output-missing-host-http.txt`), 0.28 gives `+`. With the
> lowest-direct CI job both versions run, so the test must pass on both.
> Decision: accept both - normalise the query-space encoding before comparing with the expected file.

## What was added or changed around it

- `poetry lock` alone keeps the old pins when they still satisfy the new bounds, so the lock was refreshed with
  `poetry update --lock httpx xmltodict aiofiles httpx-retries respx`. Nothing else in the lock changed apart
  from `sniffio` dropping out (httpx 0.28 no longer needs it).
- The lowest-direct CI job is not a separate job but one more entry of the existing integration matrix
  (`dependencies: lowest-direct` on MarkLogic 12.1). It installs the locked environment with poetry as the other
  entries do, then downgrades the direct dependencies with
  `uv pip install --resolution lowest-direct --upgrade -e ".[kerberos]"`, prints the installed versions, runs the
  unit suite and then the integration suite. Poetry has no lowest-version resolution, hence uv (pinned like
  poetry). The job name of the existing entries is unchanged, so required status checks keep matching; the new
  entry is `integration-tests (<image>, lowest-direct)`.
- `lowest-direct` covers every direct dependency, not only the four whose bounds changed: pydantic 2.8.2,
  pyyaml 6.0.2, cleo 2.1.0, questionary 2.1.1, python-dateutil 2.9.0.post0 and pyspnego 0.12.1 also run at
  their lower bounds. All pass locally.
- A2: the bug reaches beyond `Metadata.from_file`. `Metadata(raw=...)`, which parses the metadata MarkLogic
  returns from a documents read, leaked the declaration into the properties on xmltodict 1.x - checked against
  local MarkLogic 12.1: `properties` came back as `{'@xmlns': "{'prop': 'http://marklogic.com/xdmp/property'}",
  'color': 'red'}`. The postprocessor fixes both paths (they share `_parse_xml`); a unit test pins the raw path.

## Report

- Behaviour: mlclient now installs with httpx 0.27-0.28.x, xmltodict 0.13-1.x, aiofiles 24.1-25.x and
  httpx-retries 0.4.5-0.6.x; the lock (development and CI) uses httpx 0.28.1, xmltodict 1.0.4,
  httpx-retries 0.6.0, aiofiles 25.1.0, respx 0.22.0. XML metadata parsing ignores namespace declarations on
  every xmltodict version. No public API or CLI change.
- Files: `pyproject.toml`, `poetry.lock`, `.github/workflows/integration-test.yml`,
  `mlclient/models/documents.py`, `tests/unit/mlclient/models/test_metadata.py`,
  `tests/unit/mlclient/models/test_metadata_factory.py`,
  `tests/resources/unit/mlclient/models/test-metadata-factory/metadata-default-namespace.xml`,
  `tests/unit/mlclient/cli/commands/test_logs_command.py`.
- Tests added: `test_from_xml_file_with_default_namespace_declarations` (default and prefixed declarations at
  several depths, plus `xmlns=""`), `test_xml_namespace_declarations_are_not_read_as_properties` (raw path).
  Both, and the existing `test_from_xml_file`, fail on the base code with xmltodict 1.0.4 and pass with the fix.
- Unit suite (Python 3.11, uv venvs inside the worktree, the shared poetry venv untouched):
  - latest versions (httpx 0.28.1, xmltodict 1.0.4, httpx-retries 0.6.0, aiofiles 25.1.0): 10427 passed;
  - lowest direct versions (httpx 0.27.0, xmltodict 0.13.0, httpx-retries 0.4.5, aiofiles 24.1.0 and the
    other direct dependencies at their lower bounds): 10427 passed.
- Lint: `ruff check .` clean with the locked ruff 0.15.18.
- Integration tests: no new ones needed; not run locally. CI runs them on 10.0-11.1, 11.3.7 and 12.1 with the
  locked versions and on 12.1 with the lowest direct versions.
- Local MarkLogic 12.1: wrote a temporary document `/mlclient-v1-01/metadata-check.xml` with a collection, a
  property, a metadata value and a quality, read its metadata as XML and parsed it with `Metadata(raw=...)` on
  both xmltodict 0.13.0 and 1.0.4 - identical, correct results (base code on 1.0.4 showed the `@xmlns`
  property). The document was deleted afterwards (404 confirmed).

## Open points for the reviewer

- The lowest-direct entry adds a fourth integration run (plus a unit run) to every PR that triggers
  integration tests. If that is too much, it could run only on `main` pushes or on dependency changes.
- `Metadata.from_file` still rejects metadata saved verbatim from MarkLogic, because the root carries `uri` and
  `xsi:schemaLocation` attributes that end up as unexpected constructor arguments (`@uri`). This is the same on
  xmltodict 0.13 and 1.x and existed before this branch; `Metadata(raw=...)` is not affected. Not fixed here -
  worth an item of its own if `from_file` is meant to accept MarkLogic output.
- The lock header now says "Poetry 2.3.2" (the version available locally) instead of 2.4.2; the content format
  is the same.
- The newest ruff (not the locked one) reports `ISC004` in untouched lines of `test_logs_command.py`; this
  matters only when the ruff pin moves (Ruff linters topic).
