# Choose the operation

Read the linked workflow before generating code. CLI defaults to environment
`local`; Python manager factories use the nearest `.mlclient` ancestor and the
first configured REST connection unless an identifier is supplied.

| Need | First choice | Python | Fallback / prerequisite |
| --- | --- | --- | --- |
| Find environments / actual settings | `ml env show`, `ml env show dev --defaults` | `MLClientManager('dev').config`, `MLEnvironment.load_file` | [Configuration](configuration.md); raw file preserves comments, exposes secrets |
| Create project/global YAML | `ml env init dev`, add `--global` for personal setup | `MLEnvironment` + documented serialization | Keep secrets local; runtime HTTP settings are Python-only |
| Copy/edit alternate credentials | `ml env copy dev dev-alt --edit`; `ml env edit dev` | Manager connection overrides | Preserve comments; do not parse/dump a file just to uncomment credentials |
| Compare configurations | `ml env compare dev prod` | Inspect copied environment models | Mask secrets by default |
| Browser/server URL | `ml url -e dev` | `ml.http.base_url` | Verify chosen tier |
| Eval inline XQuery / JS | `ml eval -x '1+1'`, `ml eval -j '1+1'` | `ml.eval.xquery`, `.javascript` | [Python/CLI](python-cli.md); variables, database, timeout |
| Eval local file | `ml eval query.xqy`, `ml eval query.js` | `ml.eval.file('query.xqy')` | Runs file content, not an installed server module |
| Send arbitrary request | `ml http get /v1/config/indexes` | Named wrapper, otherwise `ml.http.get/request` | Select correct connection, check status, explicit content negotiation |
| Many independent requests | One script using AsyncMLClient | Chunked bounded `asyncio.gather` | [Templates](templates.md); bulk operations first; avoid unbounded task creation |
| Read one/many documents | `ml http get /v1/documents uri=/a.json` for inspection | `ml.documents.read('/a.json')` or list of URIs | [Documents](documents.md); parsed single model vs URI-keyed dict |
| Stream parsed documents | Python | `ml.documents.read_stream` | Async iterator still operates on buffered HTTP response; not unlimited-memory export |
| Sample structure | `ml sample invoice`, `ml sample -j` | Bounded CtsService search | Sample/projection is not a full document |
| Create/replace documents | Python `Document.*` + `.write` | Bulk list preserves type and metadata | `ml.rest.documents.post`; raw HTTP PUT; full body replacement differs from patch |
| Partial document update | REST PATCH via CLI/Python | `ml.http.request("PATCH", ...)` (no named patch wrapper) | Read PATCH contract, namespace context, optimistic concurrency headers |
| Metadata-only update | Python | `Document.metadata_update`, `Metadata`, `.write` | Preserve unmodified categories and permissions explicitly |
| Download/export documents | Python | `.read` + `DocumentsWriter.write` | Validate URI paths before writing; metadata sidecars, binary bytes |
| Upload local documents | Python | `DocumentsLoader.load` + `.write` | Check URI mapping, format and sidecars; bounded batches |
| Delete documents | Python | `.documents.delete` | URI list and category must match intended deletion |
| Atomic several operations | Python | `with ml.transaction()` / `async with await ml.transaction()` | Pass `**txn` to EVERY request; sequential dependent writes |
| Find documents or subtrees | Python CtsService / AsyncCtsService | `.search(query=..., pos=[1,25])` | `ml eval` query; REST `/v1/search` via raw HTTP for Search API snippets/facets |
| Cursor/export millions of URIs | Estimate, native lexicon pages, incremental file output | [URI workflow](uri-workflows.md), `uri_pages` template | Privileged per-host fixed forest scopes; no native limit/offset pagination |
| Find URIs | Python CTS | `.uris`, `.uri_match` | URI lexicon required; filtered search fallback for correctness |
| Find distinct values/facets | Python CTS | `.values`, `.element_values`, `.field_values` | Verify range/field index; ValueHit carries frequency |
| Count candidates | Python CTS | `.estimate` | Fast fragment estimate, not exact filtered count |
| Aggregates | Python CTS | `.sum_aggregate`, `.avg_aggregate`, `.count_aggregate` | Index reference and fragment/item frequency semantics |
| Discover indexes | Manage database properties + project `ml-config/databases` | `.manage.databases.get_properties` | Raw `/v1/config/indexes`, `view=describe-indexes`; see [Search](search.md) |
| Check health | `ml health -e dev` | `.healthcheck()` | Health uses dedicated configuration; bounded outer deadline |
| Server version | `ml version -e dev` | Sync `.version`, async `await .version()` | Match major-version REST contracts |
| Logs | `ml logs -e dev --all-hosts` | `LogsService` / `AsyncLogsService(ml.manage)` | [Log investigation](logs.md); narrow time/regex/host, check rotation |
| Log level / trace flags | `ml log-level`, `ml trace-events` | Dedicated diagnostic services | These standalone services have sync APIs; do not invent async methods |
| Database/forest/host status | Named Manage API | `.manage.databases.get(..., view='status', data_format='json')` | Endpoint navigator for exact supported views |
| Update database/server config | Named Manage `.put_properties` | Read properties, apply narrow body, check response | Changes can require restart or trigger reindexing |
| Bootstrap/join host | Admin contract | `.admin.call(CustomCall)` or raw Admin client | No automatic provisioning; explicit operator workflow |
| Custom app endpoint | `.http` for one-off call | ApiCall → wrapper → custom RestApi/client | [Extensions](extensions.md); service only if parsing/orchestration adds value |

General fallback: select environment/connection → construct request with explicit
query/body/header types → send → `raise_for_status`/`MLResponseParser` → parse.
Avoid `requests`, handwritten digest auth and separate HTTP sessions when the
existing client already handles the connection.
