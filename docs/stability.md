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
integration matrix runs against one pinned image per MarkLogic major line:

| MarkLogic | Docker image tag | Authentication coverage |
| --- | --- | --- |
| 10.0-11.1 | `10.0-11.1-ubi-2.2.4` | Credential, application-level, TLS, client certificate and Kerberos; JWT OAuth skipped |
| 11.3.7 | `11.3.7-ubi-2.3.0` | The same scenarios plus JWT OAuth |
| 12.1.0 | `12.1.0-ubi-2.3.0` | The same scenarios plus JWT OAuth |

All images use the `progressofficial/marklogic-db` repository. JWT Resource Server
authentication requires **11.2+**; see [Connection and authentication](user/python/connections.md).
The Cloud token flow is tested with mocked HTTP responses, not a live Cloud
deployment. CI requires the provisioned certificates and Kerberos tooling;
missing prerequisites fail the job instead of silently skipping those scenarios.

These runs validate the integration scenarios on the listed releases. They do
not establish support for every endpoint, patch release or server configuration.
MarkLogic 9 is not covered. MLClient does not perform server-version checks when
constructing a client; configure the server for the transport and auth you use.

## Release candidates

Versions use bare numeric tags, such as `1.0.0`, without a `v` prefix. Candidates
use PEP 440 suffixes such as `1.0.0rc1` or `1.0.0b1`:

```sh
pip install --pre mlclient
```

Normal installation selects stable releases when available. A candidate is for
validation before a stable release; consult its release notes before upgrading.
See [GitHub Releases](https://github.com/monasticus/mlclient/releases) for changes,
and the [release process](releasing.md) for maintainer instructions.
