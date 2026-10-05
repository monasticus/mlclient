# Complete endpoint contracts

Select the server's major version. The bundled vendor exports include the full
available endpoint sections, not merely endpoint names: parameter tables,
request and response headers, response/status descriptions, privileges, usage
notes and request examples. Body structure is described in the original usage
notes/examples where supplied; an export is not a formal complete JSON Schema.
Do not invent a schema where the vendor documentation supplies none.

| MarkLogic | Contracts | Index with library routes and exact line ranges |
| --- | --- | --- |
| 10 | [392 sections](endpoints/v10.md) | [v10 index](endpoints/v10-index.md) |
| 11 | [401 sections](endpoints/v11.md) | [v11 index](endpoints/v11-index.md) |
| 12 | [406 sections](endpoints/v12.md) | [v12 index](endpoints/v12-index.md) |

Use `rg 'METHOD /path' endpoints/v12-index.md`, then read only the reported
inclusive range of `endpoints/v12.md`. Resolve these paths relative to this
reference directory. Do not load the whole 2–3 MB document into context.

## Library support

Each index row gives the existing named Python wrapper (both sync and async),
or `Raw HTTP / custom ApiCall` when no named wrapper exists. A wrapper may not
expose all vendor parameters/views; compare its [actual signature](api-methods.md)
and validation before choosing it. Dedicated services such as DocumentsService,
EvalService and CtsService sit above those wrappers and are preferable when they
match the task. For unwrapped endpoints use the correctly configured `.http`
connection or a custom Call. The CLI `ml http` can reach any of these endpoints.

## Resolve live documentation URLs

Use `https://docs.marklogic.com/MAJOR.0/REST/METHOD/PATH` where MAJOR is 10, 11
or 12. The URL references an endpoint pattern, not a real database name.
For example:

- `https://docs.marklogic.com/12.0/REST/GET/v1/documents`
- `https://docs.marklogic.com/12.0/REST/GET/manage/v2/databases/[id-or-name]/properties`
- `https://docs.marklogic.com/11.0/REST/POST/v1/eval`

Use the exact documented placeholder spelling, not necessarily the shorthand
`{id|name}` in the export. The generated named-method reference includes the
canonical URL suffixes from MLClient's source. Variant pages may use `@` in place
of `?`, e.g. `/REST/GET/manage/v2/databases/[id-or-name]@view=status`.
If a constructed link redirects or fails, search the official site's versioned
REST index for the exact method/path. Do not reinterpret an inaccessible docs
page as an unsupported live endpoint.

Read request parameter cardinality: `+` required one-or-more, `*` optional
zero-or-more, `?` optional zero-or-one, no suffix required exactly one where the
reference uses that notation. Distinguish query parameters from form fields,
URL segments and JSON/XML bodies. Match Content-Type and Accept independently;
responses can be XML, JSON, text, multipart or binary.

## Provenance and maintenance

Endpoint text comes from the MarkLogic REST API Reference exports in the
Palamentis MarkLogic knowledge base supplied for this task. Preserve their
vendor descriptions and limitations; MLClient routing annotations are generated
from the library's public API methods. MarkLogic owns its documentation; these
references do not imply that vendor text is authored by MLClient.

Regenerate from a local source-docs directory using
`python scripts/build_skill_endpoints.py SOURCE_DOCS_DIRECTORY` in an MLClient
checkout. Regeneration must retain all sections, update line ranges and verify
that wrapper links correspond to actual supported paths. Update when adding
API wrappers or importing newer vendor documentation. Check live contracts when
server behavior differs; never silently treat an export as current for all
patch versions.
