# Contributing to MLClient

Bug reports, documentation improvements and code contributions are welcome.
You do not need a running MarkLogic server to work on the documentation or run
unit tests. For a substantial feature or a public API change, open an
[issue](https://github.com/monasticus/mlclient/issues) first so we can agree on
its scope before you invest in an implementation. Small fixes can go straight
to a pull request; draft PRs are welcome for early feedback.

## Reporting a problem

Check existing issues first. Include a minimal example, expected and actual
behavior, the MLClient and Python versions, and your operating system. For a
server issue, include the MarkLogic version, authentication method, endpoint
and relevant error code. Remove credentials, tokens, document contents and
private environment details from examples and logs.

Keep discussion respectful and focused on the problem. Explain disagreements
with examples or evidence. Maintainers decide whether a change fits the
library's scope; a useful idea may still belong in an application rather than
in MLClient.

Do not report an exploitable security issue in a public issue. Contact the
maintainer privately at the email listed in `pyproject.toml`, initially without
secrets or sensitive attachments, to arrange a disclosure channel.

## Set up a development checkout

Fork the repository, clone your fork and create a branch from the upstream
`main`. If you have write access, use a feature branch in the main repository.
Use a descriptive name such as `feature/262-documentation` or
`fix/eval-timeout`; an issue number is useful when one exists.

Use Python 3.11 and Poetry 2.2.0 to match the documentation build. Unit-test CI
also covers Python 3.10, 3.12, 3.13 and 3.14; keep library code compatible with 3.10.

```sh
poetry env use python3.11
poetry install --with docs
poetry run ml --help
poetry run pytest tests/unit -q
```

Install Poetry separately if it is not already available. Run commands with
`poetry run` so they use this checkout's environment. Keep `poetry.lock` in sync
when deliberately changing dependencies; avoid unrelated dependency upgrades.

## How the library fits together

Trace a nearby implementation from its public entry point to the HTTP request
before choosing where to put a change.

| Area | Responsibility |
| --- | --- |
| `mlclient/calls/` | Represent one request: method, path, parameters, headers and body. Calls perform no I/O. |
| `mlclient/api/` | Thin resource wrappers that send Calls and return raw responses, with sync and async counterparts. |
| `mlclient/services/` | Higher-level operations: parsed results, orchestration and resource lifecycles. |
| `mlclient/clients/` | Public clients, HTTP transport and session ownership. |
| `mlclient/http_config.py` | Resolved HTTP settings, cloning and session-sharing compatibility. |
| `mlclient/ml_environment.py`, `mlclient/connection.py`, `mlclient/auth.py` | Declarative connection settings, inheritance, validation and authentication. |
| `mlclient/ml_client_manager.py` | Resolve an environment into clients and apply runtime overrides. |
| `mlclient/cli/` | Cleo commands: parse input, call the library and format output. |
| `tests/unit/`, `tests/integration/` | Mocked behavior checks and real MarkLogic scenarios. |

A new endpoint normally needs a Call and an API wrapper. Add a service when it
provides a useful higher-level operation. Keep domain logic out of CLI commands.
The API layer is the first I/O boundary and therefore the first layer requiring
sync/async pairs; Calls themselves are synchronous request descriptions.

## Design and code quality

Prefer small, direct changes and existing helpers over new abstractions. Keep
validation at the boundary that owns the value, and preserve useful server
errors. Add a dependency only when its value justifies its maintenance and
license obligations.

Use public methods and properties rather than another object's private state,
including in tests. Keep transport options out of MarkLogic query parameters.
Do not hide errors with broad exception handling or fall back after unrelated
failures. Diagnostic logs should explain attempts and failures without exposing
credentials or sensitive payloads.

Use type annotations and NumPy-style docstrings. Public methods and nontrivial
private helpers should document parameters, return values, relevant exceptions
and surprising behavior. Each sync and async method needs its own usable
documentation; a reference to the other implementation is not enough.

Follow neighboring code and the Ruff configuration in `pyproject.toml`. Fix
lint findings rather than adding suppressions; discuss any necessary exception
in the PR. Keep formatting-only changes out of unrelated files.

## Testing a change

For a bug, start with a regression test that fails for the reported behavior.
Test observable results and failure paths, rather than mirroring implementation
steps. Keep new tests beside the relevant operation and parameter group, and
use distinct test-module basenames to avoid collection collisions.

| Test kind | What it should establish |
| --- | --- |
| Call unit tests | Correct request construction, defaults and invalid input. |
| API unit tests | Parameters, headers and bodies reach the expected HTTP route; sync and async agree. |
| Service unit tests | Parsing, orchestration, routing, cleanup and fallback boundaries. |
| CLI unit tests | Parsing, defaults, short/long options, errors, output and exit status through Cleo `CommandTester`. |
| Live API tests | HTTP status/error contracts that mocks cannot establish. |
| Live service tests | Value added by the service, such as transaction isolation or a setting round-trip. |

Reuse `MLRespXMocker` and existing document mock helpers. Match the request's
parameters or body at the mock route to prove forwarding. For HTTP options such
as timeout, inspect the resulting request extensions. Mirror affected sync and
async behavior. Coverage is line-based; aim to retain 100% line coverage, but
also test distinct requirements that happen to share a line.

```sh
# During development, select the affected module or test.
poetry run pytest tests/unit/mlclient/cli/commands/test_log_level_command.py -q

# Before submitting a code change.
poetry run pytest tests/unit --cov=mlclient --cov-report=term-missing
poetry run ruff check .
git diff --check
```

Documentation-only changes need a documentation build and
example checks, not new unit tests for prose.

### Running against MarkLogic

The integration setup provisions a disposable MarkLogic server and a Kerberos
KDC through Docker Compose. It needs Docker Compose, access to the image named
in `tests/integration/Dockerfile.marklogic`, and free host ports 88, 7997 and
8000–8012. Use a development machine; the setup uses test credentials and tests
can change server state. Do not point these tests at production.

On Ubuntu, the full authentication matrix also needs `libkrb5-dev` and
`krb5-user` installed before installing the `kerberos` extra.

```sh
poetry install --with docs --extras kerberos
docker compose -f tests/integration/docker-compose.yaml up -d --build
```

Wait until `mlclient_integration` reports `healthy`. The health check confirms
provisioning, not just an open port:

```sh
docker inspect --format '{{.State.Health.Status}}' mlclient_integration
MLCLIENT_IT_CERTS_DIR=tests/integration/.certs poetry run pytest tests/integration -ra
```

Review skips: missing certificates, OAuth configuration or Kerberos tooling can
skip authentication scenarios. Record what ran and what was unavailable in the
PR. See `.github/workflows/integration-test.yml` for the CI provisioning flow.
When finished, stop the test containers:

```sh
docker compose -f tests/integration/docker-compose.yaml down
```

Live tests must restore changed settings and delete test data in `finally`
blocks. Use generic names and dedicated test resources. Add live scenarios when
they prove a server contract or service behavior; a separate integration suite
for every Call is unnecessary. For CLI changes, also run representative commands
as actual processes and check errors and output flags where relevant.

## Common changes

### Supporting a REST endpoint

1. Check the official MarkLogic endpoint reference and the nearest Call/API pair.
   Probe enumerated parameter values on a test server before defining accepted
   values; record the server version and observed behavior in the PR.
2. Add request construction and validation in `calls/`, with unit tests. Register
   public imports and exports in `calls/__init__.py`.
3. Add sync/async resource methods in `api/`, the appropriate REST/Manage/Admin
   group accessors, and package exports. Forward HTTP request options separately
   from endpoint parameters.
4. Test the wire contract in both API variants. Add live coverage where a real
   status code, server error or behavior needs verification.
5. Update public docstrings and the Python guide. New modules enter the generated
   API reference automatically; no reference stub is needed.

### Adding or changing a CLI command

1. Reuse or implement the library operation first. Define positional arguments,
   defaults and the difference between connection selection and operation targets.
2. Register the command in `mlclient/cli/commands/__init__.py` and `mlclient/cli/app.py`.
   Follow neighboring Cleo commands and test through `CommandTester`.
3. Keep selectors consistent: `-e/--environment` selects an environment;
   `-c/--connection` selects a connection identifier or port where applicable.
   `logs -s/--server` accepts an identifier or port; `log-level -s/--server`
   takes an actual MarkLogic App Server name. Short options are command-specific.
4. Cover defaults, short/long forms, invalid values, output and exit codes.
   Escape external text used in Cleo markup; preserve raw response bodies.
5. Update the command page, CLI overview and navigation. Update README and Home
   examples when applicable, and compare documented help with `ml COMMAND --help`.

### Adding a service

Use existing API wrappers where possible. Decide which results to parse, which
errors permit fallback, and how resources are closed or restored. Match sync and
async support to the public surface being extended. Stateful transaction handles
have a lifecycle; they are not a template for every service. Update exports,
client accessors where appropriate, narrative examples and service tables.

### Changing configuration, environments or client factories

Define omitted, explicit and `None` behavior before implementing overrides.
Connection settings belong in environment models; retry, timeout and pool limits
are HTTP runtime settings exposed through HTTP configuration, clients and the
manager, not YAML environment fields.

Trace defaults and overrides through the environment, manager and both client
variants. Preserve explicit health settings and health-specific defaults.
Transport-affecting changes need session-sharing checks: matching ports alone
are insufficient. Auxiliary connections open lazily, and closing a client must
close every unique session once.

Test inheritance, invalid input, cloning, override precedence and mutation
isolation. A per-request override must not affect the next request. Environment
changes also need serialization, templates, `env init` and `env show` review.
Inspect-only commands read raw configuration so injected defaults do not appear
as if they were written in the user's file. Update setup examples and the Python
guide with basic usage before advanced overrides.

## Documentation

Authored documentation is Markdown in `docs/`. The main entry points are
`docs/index.md`, `docs/quickstart.md`, `docs/user/setup.md`, the Python task guides
under `docs/user/python/`, and the command
pages under `docs/user/cli/`. Keep README examples aligned with Home. Register
new guide pages in `mkdocs.yml`; API pages are generated from Python modules
and NumPy docstrings, including Pydantic fields and schemas.

```sh
make docs-serve
make docs-build
```

`make docs-build` runs a strict MkDocs build and checks generated pages, links,
anchors and representative API rendering. Do not commit `site/` or generated
reference pages. See the [documentation maintenance guide](https://github.com/monasticus/mlclient/blob/main/docs/documentation.md)
for build details and versioned publication.

## Pull requests, branches and releases

Target `main` and keep one coherent purpose per PR. Explain the problem, the
resulting behavior and the checks you ran. Include a small before/after example
for user-facing changes, and identify compatibility changes and unavailable
checks. Draft PRs are useful when the API design needs discussion.

Rebase your feature branch when upstream changes affect it, especially after a
PR it depends on has merged. Coordinate before rewriting a branch shared with
others. Do not include unrelated branch work or generated files. Maintainers
review scope, API consistency, tests and documentation before merging.

MLClient is currently pre-1.0. Call out breaking changes explicitly; do not assume
that every existing interface is frozen, or that a breaking change needs no
explanation. CI currently tests Python 3.10–3.14; this does not establish support
for every Python or MarkLogic version.

Releases are maintainer work. Version preparation opens a PR; tagging happens
only after it is squash-merged into `main`. Numeric tags trigger reusable test,
coverage and lint gates, artifact checks, OIDC PyPI publication and release notes.
`make publish` is retired. See the
[release process](https://github.com/monasticus/mlclient/blob/main/docs/releasing.md)
for the exact commands and one-time Trusted Publisher setup.

From 1.0.0, stable APIs and CLI commands follow SemVer. The entire jobs package
is experimental and can change in minor releases. Stable feature removal needs
a major release, a prior working deprecation with `DeprecationWarning`, and
migration guidance. See the
[stability policy](https://github.com/monasticus/mlclient/blob/main/docs/stability.md).

## License and third-party code

MLClient is currently distributed under the MIT license in `LICENSE`. Submit
code you have the right to contribute under those terms, retain required
attributions, and identify any third-party code or new dependency in the PR.
A dependency has its own license; the project's MIT declaration does not
replace its obligations.
