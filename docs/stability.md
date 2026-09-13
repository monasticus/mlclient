# API stability and compatibility

## The 1.0 contract

Starting with MLClient 1.0.0, stable public Python APIs and CLI commands follow
Semantic Versioning:

| Version change | Meaning |
| --- | --- |
| Major | A breaking public API or CLI change, including removed/renamed symbols, incompatible signatures or changed default behavior |
| Minor | A backward-compatible feature, such as a new method, optional parameter or command |
| Patch | A backward-compatible fix, documentation correction or internal refactor |

The contract covers public exports from `mlclient` and public APIs documented in
the reference. Names or modules beginning with `_` are implementation details.
The explicitly experimental jobs API is an exception described below. An import
that merely happens to expose a third-party helper is not a supported extension
point; use documented imports.

## Deprecation

A stable feature continues to work while deprecated. Its warning is a Python
`DeprecationWarning` naming the replacement and intended removal version, and
its documentation and release notes explain how to migrate. Removal or an
incompatible change happens in a major release, not a minor or patch release.
Python may hide `DeprecationWarning` by default; applications can enable it
with `python -Wd` during testing.

Dropping a Python version is treated as a minor release and announced in release
notes. This platform-support exception is separate from the API/CLI contract.

## Experimental jobs

Everything in `mlclient.jobs`, including builders and report models, remains
experimental. It may change incompatibly in a minor release while the API is
being redesigned. It is retained for existing users and remains in the generated
reference, but is not a stable workflow recommended by the user guide.

Constructing `ReadDocumentsJob` or `WriteDocumentsJob` logs a warning on that job's
module logger. Importing the package does not emit a warning. Python logging
configuration controls where that warning is displayed. Prefer
`MLClient.documents` or `AsyncMLClient.documents` for stable document operations.

## Supported and tested versions

The unit-test CI matrix covers Python 3.10, 3.11, 3.12, 3.13 and 3.14. The live
integration setup currently uses MarkLogic 11.2.0. Coverage on that server does
not establish that every endpoint and authentication combination works on every
MarkLogic release; check the server's endpoint documentation for version-specific
requirements.

## Release candidates

Versions use bare numeric tags, such as `1.0.0`, without a `v` prefix. Candidates
use PEP 440 suffixes such as `1.0.0rc1` or `1.0.0b1`:

```sh
python -m pip install --pre mlclient
```

Normal installation selects stable releases when available. A candidate is for
validation before a stable release; consult its release notes before upgrading.
See [GitHub Releases](https://github.com/monasticus/mlclient/releases) for changes,
and the [release process](releasing.md) for maintainer instructions.
