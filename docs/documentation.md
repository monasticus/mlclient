# Contributing to the documentation

Documentation changes follow the same pull-request process as code changes.
You can build the complete site locally without a MarkLogic server.

## Build and preview

Use Python 3.11 and Poetry 2.2.0, matching CI:

```sh
make docs-install
make docs-serve
make docs-build
```

The optional `docs` dependency group is resolved in `poetry.lock`. Both local
and CI installs use `poetry install --only main,docs`. To run library tests too,
install the development group with `poetry install --with docs`.

The local MkDocs preview renders a single version. The version catalog is
provided by mike only in a versioned deployment (or `mike serve`); it is not
available in the plain preview.

MkDocs runs in strict mode. Broken internal links, unresolved API references and
build warnings fail the build. The site is written to ignored `site/`; never
commit it. Material supplies light/dark themes, search and the version selector.

## Writing guides

The repository-level `CONTRIBUTING.md` is the source of the website contribution
guide. The existing generation script publishes it as `contributing.md`; edit
the root file rather than creating a second copy under `docs/`.

Write guides in Markdown under `docs/` and register them in `mkdocs.yml`.
Start with a working example; introduce configuration only when the reader
needs it. Split advanced topics into focused pages when
their detail would overwhelm the quickstart.

CLI pages follow: a short description and examples, then Arguments and Options.
Use a third-level heading for each argument or option, including its short alias,
default and meaningful constraints. Describe global options once in `user/cli.md`.
Do not paste terminal help output into authored pages. `make docs-build` checks
that each command argument, option and short alias has its own documented
heading. Keep command families nested (`env` contains `init` and `show`).
Keep `user/environments.md` focused on a basic environment and its Python usage; put
inheritance, authentication overrides and advanced examples in
`user/python/more-on-environments.md`.

Use one top-level heading per authored page, with nested headings for its
sections. Link to the shared configuration guides instead of repeating them in
individual command or Python task pages.

Keep README examples in sync with `docs/index.md`. Command help and examples
must match the CLI on the branch being documented. Use fenced code blocks,
Markdown tables and Material admonitions (`!!! note`). The example environment
is included directly from `docs/user/environments/mlclient-local.yaml`.

## Updating the API reference

`docs/gen_ref_pages.py` lists the canonical public namespaces and reads each
namespace's `__all__`. It generates one page per exported class/function and
namespace indexes for values and type aliases. Every symbol page shows the
public import; headings and anchors use that same identifier. Implementation
modules do not get their own pages. Do not add hand-maintained reference stubs.

When adding an export, update its owning namespace and
`tests/unit/mlclient/test_public_api.py`. Add a new namespace to the generator
only when the public structure needs one. `scripts/check_docs.py` verifies the
canonical pages and anchors, duplicate exports, links and representative API
rendering. NumPy-style docstrings stay in Python source; source links may point
to private modules without making those modules public imports.

Experimental job classes and report types use the internal `@experimental`
decorator. Its metadata supplies the warning notice on each reference page;
`log_on_init=True` additionally warns when a job is constructed. Report models
carry the notice without logging for every document.

`griffe-pydantic` renders model fields, validator relationships and JSON schema.

## Versioned publishing

Only `.github/workflows/docs.yml` writes the production `gh-pages` branch.
PRs run a strict build; `main` publishes `dev`. The release workflow calls this
workflow after successful package publication: stable tags publish their version
and update `latest`, while prerelease tags publish a numbered entry only.
See [Releasing MLClient](releasing.md) for release checks and tag preparation.

`make docs-deploy-dev` requests a CI run from `main` using authenticated GitHub
CLI. It does not push local docs. A failed release documentation job can be
retried through the release workflow. Republishing an older stable tag also
moves `latest`; do this only when intentionally changing the default release.

When changing documentation dependencies or deployment configuration, also
check a local versioned preview with `mike serve` to verify the version selector.
