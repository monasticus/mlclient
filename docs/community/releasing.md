# Release process

Releases are tag-driven and maintained on a single integration branch, `main`.
Use short-lived `feature/mlclient-NNN` branches and squash-merge reviewed PRs.
There is no `develop` branch. Create a maintenance branch such as `release/1.x`
only when an older major actually needs a supported patch.

## Prepare, review, then tag

Maintainers prepare the version in a pull request and publish it after review.
Use Poetry 2.2.0 and an authenticated GitHub CLI (`gh`):

```sh
git switch main
git pull --ff-only
poetry install --with docs
make release-minor
```

`release-patch`, `release-minor` and `release-major` use Poetry's version
arithmetic. They require a clean `main` equal to `origin/main`, create a
`feature/release-X.Y.Z` branch, synchronize versions, commit only version files,
push that branch and open a PR using authenticated `gh`. They never commit or
push a version change directly to `main`.

For a candidate, specify the exact version; a generic prerelease increment does
not necessarily produce the intended major or `rc` phase:

```sh
make release-pre VERSION=1.0.0rc1
```

Poetry remains the version tool. The pinned project plugin
`poetry-bumpversion` synchronizes `mlclient/_version.py`; Poetry updates
`pyproject.toml` itself. README uses version-independent links. The helper
checks that the exported version matches the package version before committing or tagging. A prepared 1.x candidate is marked
Beta in package metadata; a stable 1.x version is marked Production/Stable.
Installing dependencies with Poetry 2.2.0 makes the required plugin available.

After required checks pass, squash-merge the version PR. Then:

```sh
git switch main
git pull --ff-only
make release-tag
```

This pushes an annotated tag matching both version files. It refuses a dirty
checkout, an unmerged local commit, a feature branch or an existing tag. Tags
are not moved. The target deliberately does not publish from your machine.

## What CI does

`.github/workflows/release.yml` validates the tag syntax, version consistency and
that its commit is reachable from `origin/main`. It then runs the reusable lint,
Python 3.10–3.14 unit/100%-coverage matrix and live integration workflows.

Only after those gates succeed does CI build documentation, a wheel and an sdist.
It installs the wheel in a clean environment outside the checkout, verifies the
import/version and CLI entry point, and checks installed dependencies. The same
uploaded distributions are passed to PyPI publishing and attached to the GitHub
Release; publishing does not rebuild them.

PyPI uses OIDC Trusted Publishing with the `pypi` environment. No stored API token
is needed. GitHub release notes are generated from merged PRs and grouped by
`breaking`, `feature`/`enhancement`, `fix`/`bug`, and `docs`/`documentation` labels.
Conventional Commits are not required. Review important migration notes before
announcing a release; generated categories do not explain compatibility for you.

After publication, the reusable documentation workflow publishes the tagged
version. Stable versions update `latest`; `a`, `b` and `rc` versions get their
own docs entry without replacing stable `latest`. Main-branch pushes still
publish `dev`. A TestPyPI run does not publish a GitHub Release or release docs.

## TestPyPI and recovery

A manual run of `release.yml` always targets TestPyPI. Select an existing numeric
release or prerelease tag, not a branch:

```sh
gh workflow run release.yml --ref 1.0.0rc1
```

Run this for a tag already present in the repository. It does not turn the tag
push into a dry run: pushing a release tag normally triggers production PyPI.

If tests fail, fix the source through a PR and prepare a new version. Do not
move the old tag. If registry publication succeeded but a later job failed,
use **Re-run failed jobs** so the successful PyPI upload is not repeated.
PyPI versions are immutable. A Pages failure can be retried independently.
