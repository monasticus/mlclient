---
name: mlclient
description: Work with MarkLogic using MLClient CLI and Python, synchronously or asynchronously. Use for evaluating XQuery or server-side JavaScript, finding URIs/documents/indexed values, importing/exporting data, configuring environments and connections, monitoring health/logs, administering servers, or extending application APIs. Includes complete MarkLogic 10–12 REST endpoint contracts.
---

# MLClient: MarkLogic operations and development

Use MLClient for the whole workflow: inspect configuration, choose a connection,
perform the operation, and check the result. Use CLI for terminal work and Python for
reusable workflows. Prefer async Python for reusable jobs,
bulk work, controlled concurrency and full document fidelity.

## Start with the task

1. Identify the installed version and invocation (`ml`, `poetry run ml`, or the
   project's virtual environment). Run `ml --help` and relevant command help.
   Respect project conventions before the styles in this skill.
2. Inspect environments with `ml env show` and `ml env show NAME --defaults`.
   Identify the actual `.mlclient` directory and target database. Inspect masked
   output first; do not include passwords or raw config in generated reports.
3. Choose the highest layer that fits: dedicated CLI command or Python service,
   named API wrapper, then raw HTTP or server-side eval. Batch compatible reads
   and writes before introducing parallel requests.
4. Load only the relevant references below. Check signatures against the
   installed library if it differs from the bundled reference.
5. Keep one client open per connection context. Bound concurrent work, await
   cancellation before closing clients, check raw response status, and distinguish
   transport timeout from an overall operation deadline.
6. Verify with a narrow request or a test at the HTTP boundary. Report unavailable
   live servers honestly; do not turn synthetic test payloads into server facts.

## Navigation

| Need | Load |
| --- | --- |
| Task → simplest CLI/Python route and fallback | [Use cases](references/use-cases.md) |
| YAML, global/project discovery, credentials, connection/auth/TLS, retry/timeout/limits | [Configuration](references/configuration.md) |
| Inline/file XQuery and JavaScript, raw requests, sync/async lifecycle | [Python and CLI](references/python-cli.md) |
| Bulk documents, metadata, patching, local export/import, transactions | [Documents](references/documents.md) |
| Query design, fragment correlation, counts/aggregates and execution cost | [Query planning](references/query-planning.md) |
| URI cursors, large file exports and privileged host/forest worker flow | [URI workflows](references/uri-workflows.md) |
| Pure Python query builders and async implementation choices | [Python builders](references/python-builders.md) |
| Index discovery, cts builders, URIs/values/aggregates, filtering and profiling | [Search and indexes](references/search.md) |
| Cluster incident logs, rotations, access/request/audit, CLI and async reports | [Logs](references/logs.md) |
| Project layout, ml-gradle configuration, index and module discovery | [ml-gradle projects](references/ml-gradle.md) |
| Choose public namespaces and inspect installed signatures | [Python API map](references/api-coverage.md) |
| Health/version/logs/status/properties/restarts/security | [Administration](references/administration.md) |
| XQuery types, nodes/JSON, transformations, updates, modules and tests | [XQuery recipes](references/xquery-recipes.md) |
| TDE/Optic, RDF/SPARQL, temporal, geo/vector and ingestion models | [Data models](references/data-models.md) |
| Correct, readable XQuery and server-side JavaScript | [MarkLogic code](references/marklogic-code.md) |
| Custom Calls, named project APIs and sync/async client subclasses | [Extensions](references/extensions.md) |
| Skill installation, supported agents and updates | [AI integration](references/ai-integration.md) |
| Every named wrapper with actual signatures | [API methods](references/api-methods.md) |
| Complete endpoint parameters, headers, responses, bodies and versioned docs links | [Endpoint navigator](references/endpoints.md) |
| Ready-to-adapt scripts and XQuery | [Templates](references/templates.md) |

For endpoint details, select the server's major version, search its index, and
read only that endpoint's line range. Do not load all three complete references.
Example: `rg 'GET /v1/documents' references/endpoints/v12-index.md`, then
`sed -n 'START,ENDp' references/endpoints/v12.md` using the reported numbers.
Paths are relative to this skill, not the user's project.

## Essential correctness rules

- Import clients from `mlclient`; import other types from their thematic public
  namespaces. Avoid private modules and removed root exports.
- Keep content requests on a REST App Server, management on Manage, bootstrap
  operations on Admin, and probes on Health. A raw `/manage/v2/…` path does not
  switch connections automatically.
- Build supported queries with `mlclient.functions.xqy`; keep substantial native
  code in separate `.xqy`/`.sjs` files. Bind external values instead of
  concatenating them into XQuery, JavaScript or
  URLs. Treat raw query expressions as executable code. Use expanded QNames for
  namespaced external XQuery variables.
- Prefer filtered search for correct documents/subtrees. Index candidates,
  lexicon frequencies and estimates are not automatically exact document counts.
  Verify index type, namespace, collation and fragment scope before range queries.
- Preserve document metadata and content types. Do not write a truncated preview,
  projected search hit or binary preview back as an original document.
- Read current state before configuration changes; send the narrow intended
  patch, retain unrelated settings, and check restart/reindex consequences.
- Keep mutation within the user's requested scope. Do not provision servers,
  install modules or change indexes merely to make an example succeed.

Public documentation: https://monasticus.github.io/mlclient/ (guides and canonical
API imports). Consult the matching MarkLogic major-version contracts through the
bundled endpoint navigator when an endpoint behaves differently.
