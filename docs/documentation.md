# Maintaining the documentation

## Build and preview

Use Python 3.11 and Poetry 2.2.0, matching CI:

```sh
make docs-install
make docs-serve
make docs-build
```

The optional `docs` dependency group is resolved in `poetry.lock`. Navigation
plugins are bounded to MkDocs-based releases; upgrade them together and rerun
the versioned deployment smoke test rather than introducing another renderer. Both local
and CI installs use `poetry install --only main,docs`. To run library tests too,
install the development group with `poetry install --with docs`.

The local MkDocs preview renders a single version. The version catalog is
provided by mike only in a versioned deployment (or `mike serve`); it is not
available in the plain preview.

MkDocs runs in strict mode. Broken internal links, unresolved API references and
build warnings fail the build. The site is written to ignored `site/`; never
commit it. Material supplies light/dark themes, search and the version selector.

## Content and API reference

Write guides in Markdown under `docs/` and register them in `mkdocs.yml`.
Keep README examples in sync with `docs/index.md`. Command help and examples
must match the CLI on the branch being documented. Use fenced code blocks,
Markdown tables and Material admonitions (`!!! note`). The example environment
is included directly from `docs/user/setup/mlclient-local.yaml`.

`docs/gen_ref_pages.py` discovers every Python module in `mlclient/`, excluding
only executable `__main__` modules. Package `__init__` files become index pages.
It generates the reference pages and navigation during the build; do not add
per-module stub files. NumPy-style docstrings stay in Python source.

`griffe-pydantic` renders model fields, validator relationships and JSON schema.
The documentation-only Griffe extension fences legacy Cleo usage sections and
recognizes that the HTTP constructors document forwarded `**kwargs`. It does
not change Python source, signatures or runtime behavior. Keep adaptations
narrow rather than silencing all parser or reference warnings.

## Versioned publishing

Only `.github/workflows/docs.yml` writes the production `gh-pages` branch.

- Pull requests run a strict build without publishing.
- Pushes to `main` publish `dev`.
- Release tags `X.Y.Z` publish that version from the tag's source and move
  `latest` to it. Until the first release, the root redirects to `dev`; after a
  release it redirects to `latest`.
- `make docs-deploy-dev` requests a CI run from `main` using an authenticated
  GitHub CLI; it does not push local documentation. A manual workflow run from
  `main` republishes `dev`. Re-run a release workflow
  against its tag to retry that release. Publishing an older tag also moves
  `latest`, so do this only when intentionally changing the default release.

The `mike` version catalog and all generated releases live in `gh-pages`.
The workflow exports the entire catalog, uploads a Pages artifact and deploys
it using GitHub's official Pages actions. Aliases use copies, so the artifact
contains no symlinks. Deployment runs share a concurrency group to avoid
competing writes; check Actions if several releases are requested together.

This differs from branch-triggered Pages publishing: pushes with
`GITHUB_TOKEN` do not trigger a branch Pages build. The Actions workflow needs
`contents: write`, `pages: write`, and `id-token: write`; PR builds remain read-only.

## One-time rollout

1. Merge this migration into `main`.
2. In **Settings → Pages → Source**, select **GitHub Actions**. Ensure repository
   policy allows the workflow permissions and the `github-pages` environment
   permits main and release-tag deployments.
3. Run the Documentation workflow from `main` (or rerun its initial failed
   deployment if Pages was not configured yet).
4. Verify the home page, all guides, API models, search and version selector at
   <https://monasticus.github.io/mlclient/>. Initially the only version is `dev`.
5. Publish a new release tag containing the migration; verify `latest`, its
   numbered release, and `dev` in the selector. Confirm older URLs still work.
6. Decommission Read the Docs only after the replacement has been checked.

Do not bootstrap `0.4.1` by building the current development source under that
name. Historical releases require their original source plus a deliberate docs
backport; new tags must include this workflow and Markdown configuration.

## Rollback

The source is independent of `gh-pages`. A failed build never reaches deployment;
the previous deployed Pages artifact stays available. A failure after writing
`gh-pages` can be retried by rerunning the workflow.

To return to RTD hosting, retain MkDocs and restore a minimal `.readthedocs.yaml`
with `mkdocs.configuration: mkdocs.yml`. Install the project and its locked docs
group in the RTD build. RTD then manages versions; disable this Pages deployment
workflow to avoid publishing to two hosts unintentionally. The old Sphinx source
remains available in Git history and does not need to remain in the source tree.
