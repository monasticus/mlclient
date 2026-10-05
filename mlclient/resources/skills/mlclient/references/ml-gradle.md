# Understand a MarkLogic project before querying it

## Reconnaissance

Read `build.gradle`/`build.gradle.kts`, settings and Gradle wrapper versions,
then project properties and environment overlays. Identify the application,
content/modules/schemas databases, REST App Servers and authentication. Inspect
custom tasks and subprojects before assuming the default layout. Environment
property overlays depend on the project's applied properties plugin/configuration.

Use `rg --files` and targeted `rg` searches; do not print credential files into
reports. `ml env init dev --from-gradle=dev` can derive an MLClient environment
from project files. Inspect its result with `ml env show dev --defaults`; the
importer does not execute arbitrary Gradle configuration or reproduce every
custom plugin, dynamic property and credential source.

| Default location | What it tells you |
| --- | --- |
| `src/main/ml-config/databases/` | Database identities, indexes, lexicons, forests and database associations |
| `src/main/ml-config/servers/`, `rest-api.json` | App Server ports, database bindings and authentication |
| `src/main/ml-config/security/` | Application roles, privileges and document defaults |
| `src/main/ml-modules/root/` | XQuery/SJS modules, namespaces and application data/query patterns |
| `src/main/ml-modules/services/` | Custom REST resource extensions |
| `src/main/ml-modules/transforms/`, `options/` | Document transforms and named Search API options |
| `src/main/ml-schemas/`, often `tde/` | XML schemas and TDE templates/views |
| `src/main/ml-data/` | Seed/input data and useful example document shapes |
| `src/test/ml-modules/` | Server-side test suites, fixtures and setup/teardown conventions |

Paths can change via `mlConfigPaths`, `mlModulePaths`, `mlSchemaPaths`, build
configuration and subprojects. Token strings such as `%%mlAppName%%` are not
resolved names; inspect token overrides and environment properties. Configuration
may be JSON or XML, and JSON comment support depends on configuration. Do not
rewrite source files just to discover the resolved setting.

## Turn project knowledge into a query

1. Find the intended content database and REST App Server, not merely the first
   name containing “content”. Verify the live App Server database binding.
2. Inspect range element/element-attribute/path/field indexes: QName namespace,
   scalar type, collation and path namespace mappings matter. Inspect URI and
   collection lexicons, word/field settings and position indexes separately.
3. Read sample document fixtures and modules for root names, JSON property names,
   collection conventions and permissions. An index name alone is not a schema.
4. Compare declared indexes with deployed Manage database properties through
   `ml.manage.databases.get_properties(name, data_format='json')`. Read current
   status/reindex progress when settings recently changed. Source configuration
   expresses intent; it does not prove deployment or completion.
5. Choose the matching CTS reference/query and validate on a small result set.
   Use [search guidance](search.md) and [code conventions](marklogic-code.md).
   For TDE views inspect schema/view/column definitions and namespaces before
   writing Optic joins or aggregations; check template deployment in the schemas
   database and the content database's schemas association.

REST resources under `services/` can often provide a simpler application-level
route than rebuilding their logic with eval. Invoke through the existing client
and documented `/v1/resources/NAME` contract; preserve `rs:` parameter names.
For transforms and search options use their corresponding REST contracts.

## Deployment and tests

Prefer the project's `./gradlew` and check its available tasks rather than
assuming every plugin version has the same tasks. `mlLoadModules` is the usual
module-loading route; index/configuration changes use the appropriate deployment
tasks. Incremental module loading need not remove deleted server modules.
Clearing/reloading databases, deploying security or changing indexes is a
separate mutation from inspecting/querying the project.

MarkLogic unit tests commonly live under `root/test/suites` inside test module
paths. Reuse assertions and setup/teardown patterns; test data belongs in the
intended test database. A suite runner can mutate state. Test query cardinality,
namespace/type boundaries, missing values, update behaviour and permissions,
not just a successful example. Python HTTP tests verify MLClient composition;
only server-side execution verifies native XQuery behaviour and indexes.

Primary project references: [layout](https://github.com/marklogic/ml-gradle/wiki/Project-layout),
[configuration](https://github.com/marklogic/ml-gradle/wiki/Configuring-ml-gradle),
[properties](https://github.com/marklogic/ml-gradle/wiki/Property-reference),
[tasks](https://github.com/marklogic/ml-gradle/wiki/Task-reference).
